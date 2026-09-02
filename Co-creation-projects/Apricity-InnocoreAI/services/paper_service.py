"""Диссертационная служба"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from ..core.database import get_db
from ..core.vector_store import VectorStore
from ..models.paper import PaperDB, Paper, PaperCreate, PaperUpdate, PaperSearch
from ..core.exceptions import PaperNotFoundError, PaperAlreadyExistsError
from ..utils.pdf_parser import PDFParser
from ..utils.embedding import EmbeddingService
import json

class PaperService:
    """Бумажные услуги"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStore()
        self.pdf_parser = PDFParser()
        self.embedding_service = EmbeddingService()
    
    def get_paper_by_id(self, paper_id: int) -> Optional[Paper]:
        """Получить документы по удостоверению личности"""
        paper_db = self.db.query(PaperDB).filter(PaperDB.id == paper_id).first()
        if not paper_db:
            raise PaperNotFoundError(f"Paper with id {paper_id} not found")
        return Paper.from_orm(paper_db)
    
    def get_papers_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> List[Paper]:
        """Получить список бумаг пользователя"""
        papers_db = self.db.query(PaperDB).filter(
            PaperDB.user_id == user_id
        ).offset(skip).limit(limit).all()
        return [Paper.from_orm(paper) for paper in papers_db]
    
    def create_paper(self, paper_create: PaperCreate, user_id: int) -> Paper:
        """Создать бумажную запись"""
        # Проверяем, существует ли уже DOI
        if paper_create.doi:
            existing = self.db.query(PaperDB).filter(PaperDB.doi == paper_create.doi).first()
            if existing:
                raise PaperAlreadyExistsError(f"Paper with DOI {paper_create.doi} already exists")
        
        # Проверяем, существует ли уже идентификатор arXiv
        if paper_create.arxiv_id:
            existing = self.db.query(PaperDB).filter(PaperDB.arxiv_id == paper_create.arxiv_id).first()
            if existing:
                raise PaperAlreadyExistsError(f"Paper with arXiv ID {paper_create.arxiv_id} already exists")
        
        #Создать бумажную запись
        paper_db = PaperDB(
            title=paper_create.title,
            authors=json.dumps(paper_create.authors),
            abstract=paper_create.abstract,
            keywords=json.dumps(paper_create.keywords),
            publication_year=paper_create.publication_year,
            journal=paper_create.journal,
            doi=paper_create.doi,
            arxiv_id=paper_create.arxiv_id,
            pdf_url=paper_create.pdf_url,
            user_id=user_id
        )
        
        self.db.add(paper_db)
        self.db.commit()
        self.db.refresh(paper_db)
        
        # Асинхронная обработка PDF и встраивание
        self._process_paper_async(paper_db.id)
        
        return Paper.from_orm(paper_db)
    
    def update_paper(self, paper_id: int, paper_update: PaperUpdate) -> Paper:
        """Обновить информацию о бумаге"""
        paper_db = self.db.query(PaperDB).filter(PaperDB.id == paper_id).first()
        if not paper_db:
            raise PaperNotFoundError(f"Paper with id {paper_id} not found")
        
        #Обновить поля
        update_data = paper_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field in ['authors', 'keywords']:
                setattr(paper_db, field, json.dumps(value))
            else:
                setattr(paper_db, field, value)
        
        self.db.commit()
        self.db.refresh(paper_db)
        
        return Paper.from_orm(paper_db)
    
    def delete_paper(self, paper_id: int) -> bool:
        """Удалить бумагу"""
        paper_db = self.db.query(PaperDB).filter(PaperDB.id == paper_id).first()
        if not paper_db:
            raise PaperNotFoundError(f"Paper with id {paper_id} not found")
        
        # Удалить из векторного хранилища
        if paper_db.embeddings:
            self.vector_store.delete_document(paper_id)
        
        self.db.delete(paper_db)
        self.db.commit()
        
        return True
    
    def search_papers(self, search: PaperSearch, user_id: int) -> List[Paper]:
        """Поиск документов"""
        query = self.db.query(PaperDB).filter(PaperDB.user_id == user_id)
        
        # Текстовый поиск
        if search.query:
            search_filter = or_(
                PaperDB.title.contains(search.query),
                PaperDB.abstract.contains(search.query),
                PaperDB.keywords.contains(search.query)
            )
            query = query.filter(search_filter)
        
        # Применить фильтр
        filters = search.filters
        if 'year_range' in filters:
            start_year, end_year = filters['year_range']
            query = query.filter(
                and_(
                    PaperDB.publication_year >= start_year,
                    PaperDB.publication_year <= end_year
                )
            )
        
        if 'venues' in filters:
            query = query.filter(PaperDB.journal.in_(filters['venues']))
        
        if 'authors' in filters:
            author_filter = or_(*[
                PaperDB.authors.contains(author) for author in filters['authors']
            ])
            query = query.filter(author_filter)
        
        # Сортировать
        if search.sort_by == "relevance":
            query = query.order_by(desc(PaperDB.relevance_score))
        elif search.sort_by == "quality":
            query = query.order_by(desc(PaperDB.quality_score))
        elif search.sort_by == "year":
            query = query.order_by(desc(PaperDB.publication_year))
        else:
            query = query.order_by(desc(PaperDB.created_at))
        
        # Пагинация
        papers_db = query.offset(search.offset).limit(search.limit).all()
        return [Paper.from_orm(paper) for paper in papers_db]
    
    def semantic_search(self, query: str, user_id: int, limit: int = 10) -> List[Paper]:
        """Бумага семантического поиска"""
        # Генерируем вектор запроса
        query_embedding = self.embedding_service.get_embedding(query)
        
        # Поиск в векторном хранилище
        results = self.vector_store.search(query_embedding, user_id, limit)
        
        # Получите соответствующую бумагу
        paper_ids = [result['id'] for result in results]
        papers_db = self.db.query(PaperDB).filter(
            and_(
                PaperDB.id.in_(paper_ids),
                PaperDB.user_id == user_id
            )
        ).all()
        
        # Сортировка по сходству
        paper_dict = {paper.id: paper for paper in papers_db}
        sorted_papers = []
        for result in results:
            if result['id'] in paper_dict:
                paper = Paper.from_orm(paper_dict[result['id']])
                paper.relevance_score = result['score']
                sorted_papers.append(paper)
        
        return sorted_papers
    
    def _process_paper_async(self, paper_id: int):
        """Асинхронная обработка документов (парсинг и встраивание PDF-файлов)"""
        try:
            paper_db = self.db.query(PaperDB).filter(PaperDB.id == paper_id).first()
            if not paper_db:
                return
            
            # Если есть URL-адрес PDF, загрузите и проанализируйте его
            if paper_db.pdf_url and not paper_db.full_text:
                full_text = self.pdf_parser.parse_pdf_from_url(paper_db.pdf_url)
                if full_text:
                    paper_db.full_text = full_text
            
            # Генерация встраивания
            text_to_embed = paper_db.title + " " + (paper_db.abstract or "")
            if paper_db.full_text:
                text_to_embed += " " + paper_db.full_text
            
            embedding = self.embedding_service.get_embedding(text_to_embed)
            paper_db.embeddings = embedding.tolist()
            
            #Добавить в векторное хранилище
            self.vector_store.add_document(
                doc_id=paper_id,
                embedding=embedding,
                metadata={
                    'title': paper_db.title,
                    'user_id': paper_db.user_id
                }
            )
            
            paper_db.is_processed = True
            self.db.commit()
            
        except Exception as e:
            print(f"Error processing paper {paper_id}: {e}")
            # Здесь вы можете добавить регистрацию ошибок
    
    def get_paper_statistics(self, user_id: int) -> Dict[str, Any]:
        """Получить бумажную статистику"""
        total_papers = self.db.query(PaperDB).filter(PaperDB.user_id == user_id).count()
        processed_papers = self.db.query(PaperDB).filter(
            and_(PaperDB.user_id == user_id, PaperDB.is_processed == True)
        ).count()
        
        # Статистика по годам
        year_stats = self.db.query(
            PaperDB.publication_year,
            self.db.func.count(PaperDB.id)
        ).filter(PaperDB.user_id == user_id).group_by(PaperDB.publication_year).all()
        
        # Статистика по журналам
        journal_stats = self.db.query(
            PaperDB.journal,
            self.db.func.count(PaperDB.id)
        ).filter(PaperDB.user_id == user_id).group_by(PaperDB.journal).all()
        
        return {
            'total_papers': total_papers,
            'processed_papers': processed_papers,
            'processing_rate': processed_papers / total_papers if total_papers > 0 else 0,
            'year_distribution': dict(year_stats),
            'journal_distribution': dict(journal_stats)
        }