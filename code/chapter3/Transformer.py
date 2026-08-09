import torch
import torch.nn as nn
import math
import copy

class MultiHeadAttention(nn.Module):
    """
    Модуль механизма многоголового внимания
    """
    def __init__(self, d_model, num_heads):
        super(MultiHeadAttention, self).__init__()
        assert d_model % num_heads == 0, "d_model должна делиться на num_heads"
        
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        # Уровень линейного преобразования, определяющий Q, K, V и выход
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        
    def scaled_dot_product_attention(self, Q, K, V, mask=None):
        # 1. Подсчитайте оценку внимания (QK^T)
        attn_scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        
        # 2. Нанесите маску (если имеется).
        if mask is not None:
            # Установите для позиции 0 в маске очень маленькое отрицательное число, чтобы оно было близко к 0 после softmax.
            attn_scores = attn_scores.masked_fill(mask == 0, -1e9)
        
        # 3. Рассчитать вес внимания (Softmax)
        attn_probs = torch.softmax(attn_scores, dim=-1)
        
        # 4. Взвешенная сумма (вес * В)
        output = torch.matmul(attn_probs, V)
        return output
        
    def split_heads(self, x):
        # Преобразование формы ввода x из (batch_size, seq_length, d_model)
        # Преобразовано в (batch_size, num_heads, seq_length, d_k)
        batch_size, seq_length, d_model = x.size()
        return x.view(batch_size, seq_length, self.num_heads, self.d_k).transpose(1, 2)
        
    def combine_heads(self, x):
        # Измените форму ввода x с (batch_size, num_heads, seq_length, d_k)
        # Вернитесь к (batch_size, seq_length, d_model).
        batch_size, num_heads, seq_length, d_k = x.size()
        return x.transpose(1, 2).contiguous().view(batch_size, seq_length, self.d_model)
        
    def forward(self, Q, K, V, mask=None):
        # 1. Выполнить линейное преобразование на Q, K, V
        Q = self.split_heads(self.W_q(Q))
        K = self.split_heads(self.W_k(K))
        V = self.split_heads(self.W_v(V))
        
        # 2. Рассчитать масштабируемое скалярное произведение внимания
        attn_output = self.scaled_dot_product_attention(Q, K, V, mask)
        
        # 3. Объедините выходные данные нескольких головок и выполните окончательное линейное преобразование.
        output = self.W_o(self.combine_heads(attn_output))
        return output

class PositionWiseFeedForward(nn.Module):
    """
    Сетевой модуль с прямой связью по положению
    """
    def __init__(self, d_model, d_ff, dropout=0.1):
        super(PositionWiseFeedForward, self).__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.relu = nn.ReLU()

    def forward(self, x):
        # Форма x: (batch_size, seq_len, d_model)
        x = self.linear1(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.linear2(x)
        # Окончательная форма вывода: (batch_size, seq_len, d_model)
        return x

class PositionalEncoding(nn.Module):
    """
    Добавьте позиционное кодирование к вектору внедрения слов входной последовательности.
    """
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Создайте достаточно длинную матрицу позиционного кодирования.
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        
        # Размер pe (позиционное кодирование) равен (max_len, d_model).
        pe = torch.zeros(max_len, d_model)
        
        # Используйте sin для четных размеров и cos для нечетных размеров.
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        # Зарегистрируйте pe как буфер, чтобы он не считался параметром модели, а перемещался вместе с моделью (например, to(device))
        self.register_buffer('pe', pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x.size(1) — текущая длина входной последовательности.
        # Добавить кодировку положения во входной вектор
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)

class EncoderLayer(nn.Module):
    """
    Базовый уровень кодировщика
    """
    def __init__(self, d_model, num_heads, d_ff, dropout):
        super(EncoderLayer, self).__init__()
        self.self_attn = MultiHeadAttention(d_model, num_heads)
        self.feed_forward = PositionWiseFeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x, mask):
        # 1. Бычье внимание к себе
        attn_output = self.self_attn(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_output))
        
        # 2. Сеть прямой связи
        ff_output = self.feed_forward(x)
        x = self.norm2(x + self.dropout(ff_output))
        
        return x

class DecoderLayer(nn.Module):
    """
    Базовый уровень декодера
    """
    def __init__(self, d_model, num_heads, d_ff, dropout):
        super(DecoderLayer, self).__init__()
        self.self_attn = MultiHeadAttention(d_model, num_heads)
        self.cross_attn = MultiHeadAttention(d_model, num_heads)
        self.feed_forward = PositionWiseFeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x, encoder_output, src_mask, tgt_mask):
        # 1. Маскируйте внимание быка к себе (к себе)
        attn_output = self.self_attn(x, x, x, tgt_mask)
        x = self.norm1(x + self.dropout(attn_output))
        
        # 2. Перекрестное внимание (к выходу энкодера)
        cross_attn_output = self.cross_attn(x, encoder_output, encoder_output, src_mask)
        x = self.norm2(x + self.dropout(cross_attn_output))
        
        # 3. Сеть прямой связи
        ff_output = self.feed_forward(x)
        x = self.norm3(x + self.dropout(ff_output))
        
        return x

class Encoder(nn.Module):
    def __init__(self, vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len):
        super(Encoder, self).__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout, max_len)
        self.layers = nn.ModuleList([EncoderLayer(d_model, num_heads, d_ff, dropout) for _ in range(num_layers)])
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, mask):
        x = self.embedding(x)
        x = self.pos_encoder(x)
        for layer in self.layers:
            x = layer(x, mask)
        return self.norm(x)

class Decoder(nn.Module):
    def __init__(self, vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len):
        super(Decoder, self).__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout, max_len)
        self.layers = nn.ModuleList([DecoderLayer(d_model, num_heads, d_ff, dropout) for _ in range(num_layers)])
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, encoder_output, src_mask, tgt_mask):
        x = self.embedding(x)
        x = self.pos_encoder(x)
        for layer in self.layers:
            x = layer(x, encoder_output, src_mask, tgt_mask)
        return self.norm(x)

class Transformer(nn.Module):
    def __init__(self, src_vocab_size, tgt_vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len=5000):
        super(Transformer, self).__init__()
        self.encoder = Encoder(src_vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len)
        self.decoder = Decoder(tgt_vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len)
        self.final_linear = nn.Linear(d_model, tgt_vocab_size)
    
    def generate_mask(self, src, tgt):
        # src_mask: (batch_size, 1, 1, src_len)
        src_mask = (src != 0).unsqueeze(1).unsqueeze(2) 
        
        # tgt_mask: (batch_size, 1, tgt_len, tgt_len)
        tgt_pad_mask = (tgt != 0).unsqueeze(1).unsqueeze(2) # (batch_size, 1, 1, tgt_len)
        tgt_len = tgt.size(1)
        # Нижняя треугольная матрица, используемая для предотвращения просмотра будущих токенов.
        tgt_sub_mask = torch.tril(torch.ones((tgt_len, tgt_len), device=src.device)).bool() # (tgt_len, tgt_len)
        tgt_mask = tgt_pad_mask & tgt_sub_mask
        
        return src_mask, tgt_mask
    
    def forward(self, src, tgt):
        src_mask, tgt_mask = self.generate_mask(src, tgt)
        
        encoder_output = self.encoder(src, src_mask)
        decoder_output = self.decoder(tgt, encoder_output, src_mask, tgt_mask)
        
        output = self.final_linear(decoder_output)
        return output

# --- Продемонстрируйте, как использовать модель ---
if __name__ == "__main__":
    # 1. Определите гиперпараметры
    src_vocab_size = 5000
    tgt_vocab_size = 5000
    d_model = 512
    num_layers = 6
    num_heads = 8
    d_ff = 2048
    dropout = 0.1
    max_len = 100
    
    # 2. Создайте экземпляр модели
    model = Transformer(src_vocab_size, tgt_vocab_size, d_model, num_layers, num_heads, d_ff, dropout, max_len)
    
    # 3. Создайте входные данные моделирования.
    # Предположим, что пакетный размер = 2, src_seq_len = 10, tgt_seq_len = 12.
    src = torch.randint(1, src_vocab_size, (2, 10))  # (batch_size, seq_length)
    tgt = torch.randint(1, tgt_vocab_size, (2, 12))  # (batch_size, seq_length)

    # 4. Модель прямого распространения
    output = model(src, tgt)
    
    # 5. Распечатайте выходную форму.
    print("Форма вывода модели:", output.shape)
    # Ожидаемый результат: torch.Size([2, 12, 5000]) -> (batch_size, tgt_seq_len, tgt_vocab_size)