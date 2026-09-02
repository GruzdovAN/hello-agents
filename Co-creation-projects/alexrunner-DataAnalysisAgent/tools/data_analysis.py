# data_analysis.py
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr, f_oneway
from hello_agents import ToolRegistry

# Загрузка набора данных
work_path = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(f"{work_path}/../data/shopping_behavior_updated.csv")

# Создание возрастных групп
def age_group(age):
    if age < 20:
        return 'Teen (<20)'
    elif age < 30:
        return '20s'
    elif age < 40:
        return '30s'
    elif age < 50:
        return '40s'
    elif age < 60:
        return '50s'
    else:
        return 'Senior (60+)'

df['Age Group'] = df['Age'].apply(age_group)

def analyze_gender_preferences(input: str) -> dict:
    """Анализ покупательских предпочтений по полу; возвращает сериализуемые типы Python"""

    # Распределение по полу
    gender_counts_dict = df['Gender'].value_counts().to_dict()

    # Средняя сумма покупок по полу
    gender_spending_series = df.groupby('Gender')['Purchase Amount (USD)'].mean()
    gender_spending_dict = gender_spending_series.to_dict()

    # Самые популярные категории товаров по полу
    gender_category = df.groupby(['Gender', 'Category']).size().unstack(fill_value=0)
    gender_category_percent = gender_category.div(gender_category.sum(axis=1), axis=0)

    # Преобразование во вложенный словарь
    gender_category_dict = gender_category_percent.to_dict('index')

    # Подготовка возвращаемого значения — только встроенные типы Python
    result = {
        'gender_distribution': gender_counts_dict,
        'average_spending_by_gender': gender_spending_dict,
        'category_preference_by_gender': gender_category_dict
    }

    # Визуализации
    visualization_urls = []

    # График распределения по полу
    plt.figure(figsize=(8, 5))
    plt.bar(gender_counts_dict.keys(), gender_counts_dict.values(), color=['blue', 'pink'])
    plt.title('Gender Distribution')
    plt.xlabel('Gender')
    plt.ylabel('Count')
    gender_distribution_path = 'figures/gender_distribution.png'
    plt.savefig(os.path.join(work_path, '../out', gender_distribution_path))
    plt.close()
    visualization_urls.append(gender_distribution_path)

    # График средней суммы покупок
    plt.figure(figsize=(8, 5))
    plt.bar(gender_spending_dict.keys(), gender_spending_dict.values(), color=['blue', 'pink'])
    plt.title('Average Spending by Gender')
    plt.xlabel('Gender')
    plt.ylabel('Average Spending (USD)')
    average_spending_path = 'figures/average_spending_by_gender.png'
    plt.savefig(os.path.join(work_path, '../out', average_spending_path))
    plt.close()
    visualization_urls.append(average_spending_path)

    # График предпочтений по категориям товаров
    gender_category.plot(kind='bar', stacked=True, figsize=(10, 6))
    plt.title('Category Preference by Gender')
    plt.xlabel('Gender')
    plt.ylabel('Count')
    category_preference_path = 'figures/category_preference_by_gender.png'
    plt.savefig(os.path.join(work_path, '../out', category_preference_path))
    plt.close()
    visualization_urls.append(category_preference_path)

    result['visualization_url'] = visualization_urls

    return result


def analyze_age_preferences(input: str) -> dict:
    age_group_counts = df['Age Group'].value_counts().sort_index()
    age_group_counts_dict = age_group_counts.to_dict()

    # Средняя сумма покупок по возрастным группам
    age_spending = df.groupby('Age Group')['Purchase Amount (USD)'].mean().sort_index()
    age_spending_dict = age_spending.to_dict()

    # Самые популярные категории товаров по возрастным группам
    age_category = df.groupby(['Age Group', 'Category']).size().unstack(fill_value=0)
    age_category_percent = age_category.div(age_category.sum(axis=1), axis=0)
    age_category_percent = age_category_percent.to_dict('index')

    result = {
        'age_group_distribution': age_group_counts_dict,
        'average_spending_by_age_group': age_spending_dict,
        'category_preference_by_age_group': age_category_percent
    }

    # Визуализации
    visualization_urls = []

    # График распределения по возрастным группам
    plt.figure(figsize=(8, 5))
    plt.bar(age_group_counts_dict.keys(), age_group_counts_dict.values(), color='skyblue')
    plt.title('Age Group Distribution')
    plt.xlabel('Age Group')
    plt.ylabel('Count')
    age_distribution_path = 'figures/age_group_distribution.png'
    plt.savefig(os.path.join(work_path, '../out', age_distribution_path))
    plt.close()
    visualization_urls.append(age_distribution_path)

    # График средней суммы покупок
    plt.figure(figsize=(8, 5))
    plt.bar(age_spending_dict.keys(), age_spending_dict.values(), color='lightgreen')
    plt.title('Average Spending by Age Group')
    plt.xlabel('Age Group')
    plt.ylabel('Average Spending (USD)')
    average_spending_path = 'figures/average_spending_by_age_group.png'
    plt.savefig(os.path.join(work_path, '../out', average_spending_path))
    plt.close()
    visualization_urls.append(average_spending_path)

    # График предпочтений по категориям товаров
    age_category.plot(kind='bar', stacked=True, figsize=(10, 6))
    plt.title('Category Preference by Age Group')
    plt.xlabel('Age Group')
    plt.ylabel('Count')
    category_preference_path = 'figures/category_preference_by_age_group.png'
    plt.savefig(os.path.join(work_path, '../out', category_preference_path))
    plt.close()
    visualization_urls.append(category_preference_path)

    result['visualization_url'] = visualization_urls  # Добавление путей к графикам в результат

    return result

def analyze_spending_differences(input: str) -> dict:
    # Статистика по полу и возрастным группам
    gender_age_spending = df.groupby(['Gender', 'Age Group'])['Purchase Amount (USD)'].mean().unstack()
    gender_age_spending_dict = gender_age_spending.to_dict()

    # Статистика по категориям товаров и возрастным группам
    category_age_spending = df.groupby(['Category', 'Age Group'])['Purchase Amount (USD)'].mean().unstack()
    category_age_spending_dict = category_age_spending.to_dict()

    result = {
        'spending_by_gender_and_age': gender_age_spending_dict,
        'spending_by_category_and_age': category_age_spending_dict
    }

    # Визуализации
    visualization_urls = []

    # График различий в расходах по полу и возрастным группам
    plt.figure(figsize=(10, 6))
    gender_age_spending.plot(kind='bar', figsize=(10, 6))
    plt.title('Average Spending by Gender and Age Group')
    plt.xlabel('Age Group')
    plt.ylabel('Average Spending (USD)')
    plt.xticks(rotation=0)
    gender_age_spending_path = 'figures/average_spending_by_gender_and_age.png'
    plt.savefig(os.path.join(work_path, '../out', gender_age_spending_path))
    plt.close()
    visualization_urls.append(gender_age_spending_path)

    # График различий в расходах по категориям и возрастным группам
    plt.figure(figsize=(10, 6))
    category_age_spending.plot(kind='bar', figsize=(10, 6))
    plt.title('Average Spending by Category and Age Group')
    plt.xlabel('Age Group')
    plt.ylabel('Average Spending (USD)')
    plt.xticks(rotation=0)
    category_age_spending_path = 'figures/average_spending_by_category_and_age.png'
    plt.savefig(os.path.join(work_path, '../out', category_age_spending_path))
    plt.close()
    visualization_urls.append(category_age_spending_path)

    result['visualization_url'] = visualization_urls  # Добавление путей к графикам в результат

    return result

def analyze_subscription_impact(input: str) -> dict:
    """
    Анализ влияния статуса подписки на расходы
    Возвращает словарь со всеми результатами анализа
    """

    # Проверка наличия столбца Subscription Status
    if 'Subscription Status' not in df.columns:
        return {"error": "В данных отсутствует столбец Subscription Status"}

    # Нормализация статуса подписки (приведение регистра)
    df['Subscription Status'] = df['Subscription Status'].str.strip().str.title()

    # 1. Базовая статистика: число подписчиков и неподписчиков
    subscription_counts = df['Subscription Status'].value_counts().to_dict()

    # 2. Сравнение средней суммы покупок
    avg_purchase_by_subscription = df.groupby('Subscription Status')['Purchase Amount (USD)'].agg(['mean', 'std', 'count']).round(2)
    avg_purchase_dict = avg_purchase_by_subscription.to_dict('index')

    # 3. Сравнение числа предыдущих покупок
    prev_purchases_by_subscription = df.groupby('Subscription Status')['Previous Purchases'].agg(['mean', 'std', 'count']).round(2)
    prev_purchases_dict = prev_purchases_by_subscription.to_dict('index')

    # 4. Различия в частоте повторных покупок (если Frequency of Purchases — числовой тип)
    frequency_analysis = {}
    if 'Frequency of Purchases' in df.columns:
        # Создание отображения частоты (для категориальных данных)
        frequency_mapping = {
            'Weekly': 52,
            'Fortnightly': 26,
            'Bi-Weekly': 26,
            'Monthly': 12,
            'Quarterly': 4,
            'Every 3 Months': 4,
            'Annually': 1
        }

        # Преобразование в числовую частоту
        df['Purchase_Frequency_Numeric'] = df['Frequency of Purchases'].map(frequency_mapping)

        frequency_by_subscription = df.groupby('Subscription Status')['Purchase_Frequency_Numeric'].agg(['mean', 'std', 'count']).round(2)
        frequency_analysis = frequency_by_subscription.to_dict('index')

    # 5. Проверка статистической значимости
    significance_tests = {}

    # Разделение данных подписчиков и неподписчиков
    subscribed = df[df['Subscription Status'] == 'Yes']
    not_subscribed = df[df['Subscription Status'] == 'No']

    # 6. Расчёт размера эффекта (Cohen's d)
    effect_sizes = {}

    if len(subscribed) > 0 and len(not_subscribed) > 0:
        # Размер эффекта для суммы покупок
        mean_diff_amount = subscribed['Purchase Amount (USD)'].mean() - not_subscribed['Purchase Amount (USD)'].mean()
        pooled_std_amount = np.sqrt(
            (subscribed['Purchase Amount (USD)'].std()**2 + not_subscribed['Purchase Amount (USD)'].std()**2) / 2
        )
        cohens_d_amount = mean_diff_amount / pooled_std_amount if pooled_std_amount > 0 else 0

        # Размер эффекта для числа предыдущих покупок
        mean_diff_prev = subscribed['Previous Purchases'].mean() - not_subscribed['Previous Purchases'].mean()
        pooled_std_prev = np.sqrt(
            (subscribed['Previous Purchases'].std()**2 + not_subscribed['Previous Purchases'].std()**2) / 2
        )
        cohens_d_prev = mean_diff_prev / pooled_std_prev if pooled_std_prev > 0 else 0

        effect_sizes = {
            'purchase_amount_cohens_d': round(cohens_d_amount, 3),
            'previous_purchases_cohens_d': round(cohens_d_prev, 3),
            'interpretation': {
                'small': 0.2,
                'medium': 0.5,
                'large': 0.8
            }
        }

    # 7. Дополнительные показатели по статусу подписки
    additional_metrics = {}

    # Сравнение перцентилей суммы покупок
    percentiles = [25, 50, 75, 90]
    for status in ['Yes', 'No']:
        status_data = df[df['Subscription Status'] == status]['Purchase Amount (USD)']
        percentile_dict = {}
        for p in percentiles:
            percentile_dict[f'p{p}'] = round(status_data.quantile(p/100), 2)
        additional_metrics[f'purchase_percentiles_{status.lower()}'] = percentile_dict

    # 8. Анализ ценности подписчиков
    value_analysis = {}
    if 'Yes' in subscription_counts and 'No' in subscription_counts:
        total_revenue_subscribed = subscribed['Purchase Amount (USD)'].sum()
        total_revenue_not_subscribed = not_subscribed['Purchase Amount (USD)'].sum()

        avg_revenue_per_customer_subscribed = total_revenue_subscribed / len(subscribed)
        avg_revenue_per_customer_not_subscribed = total_revenue_not_subscribed / len(not_subscribed)

        value_analysis = {
            'total_revenue': {
                'subscribed': round(total_revenue_subscribed, 2),
                'not_subscribed': round(total_revenue_not_subscribed, 2),
                'ratio': round(total_revenue_subscribed / total_revenue_not_subscribed, 2) if total_revenue_not_subscribed > 0 else 'N/A'
            },
            'avg_revenue_per_customer': {
                'subscribed': round(avg_revenue_per_customer_subscribed, 2),
                'not_subscribed': round(avg_revenue_per_customer_not_subscribed, 2),
                'difference': round(avg_revenue_per_customer_subscribed - avg_revenue_per_customer_not_subscribed, 2)
            }
        }

    # 9. Анализ различий в покупках по категориям (по статусу подписки)
    category_analysis = {}
    category_by_subscription = df.groupby(['Subscription Status', 'Category']).size().unstack(fill_value=0)

    # Доля подписчиков в каждой категории
    for category in category_by_subscription.columns:
        total_category = category_by_subscription[category].sum()
        if total_category > 0:
            subscribed_pct = (category_by_subscription.loc['Yes', category] / total_category * 100) if 'Yes' in category_by_subscription.index else 0
            not_subscribed_pct = (category_by_subscription.loc['No', category] / total_category * 100) if 'No' in category_by_subscription.index else 0
            category_analysis[category] = {
                'subscribed_pct': round(subscribed_pct, 1),
                'not_subscribed_pct': round(not_subscribed_pct, 1),
                'subscribed_count': int(category_by_subscription.loc['Yes', category]) if 'Yes' in category_by_subscription.index else 0,
                'not_subscribed_count': int(category_by_subscription.loc['No', category]) if 'No' in category_by_subscription.index else 0
            }

    # Объединение всех результатов в один словарь
    results = {
        'basic_stats': {
            'subscription_counts': subscription_counts,
            'subscribed_percentage': round(subscription_counts.get('Yes', 0) / len(df) * 100, 1) if len(df) > 0 else 0
        },
        'purchase_amount_comparison': avg_purchase_dict,
        'previous_purchases_comparison': prev_purchases_dict,
        'purchase_frequency_analysis': frequency_analysis,
        'statistical_significance': significance_tests,
        'effect_sizes': effect_sizes,
        'percentile_analysis': additional_metrics,
        'customer_value_analysis': value_analysis,
        'category_preference_by_subscription': category_analysis,
        'summary': {
            'total_customers': len(df),
            'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_columns_used': ['Subscription Status', 'Purchase Amount (USD)', 'Previous Purchases', 'Frequency of Purchases', 'Category']
        }
    }

    # Визуализации
    visualization_urls = []

    # Сравнение средней суммы покупок подписчиков и неподписчиков
    plt.figure(figsize=(8, 5))
    avg_purchase_by_subscription['mean'].plot(kind='bar', color=['blue', 'orange'])
    plt.title('Average Purchase Amount by Subscription Status')
    plt.xlabel('Subscription Status')
    plt.ylabel('Average Purchase Amount (USD)')
    purchase_amount_path = 'figures/average_purchase_by_subscription.png'
    plt.savefig(os.path.join(work_path, '../out', purchase_amount_path))
    plt.close()
    visualization_urls.append(purchase_amount_path)

    # Сравнение числа предыдущих покупок подписчиков и неподписчиков
    plt.figure(figsize=(8, 5))
    prev_purchases_by_subscription['mean'].plot(kind='bar', color=['blue', 'orange'])
    plt.title('Average Previous Purchases by Subscription Status')
    plt.xlabel('Subscription Status')
    plt.ylabel('Average Previous Purchases')
    previous_purchases_path = 'figures/average_previous_purchases_by_subscription.png'
    plt.savefig(os.path.join(work_path, '../out', previous_purchases_path))
    plt.close()
    visualization_urls.append(previous_purchases_path)

    results['visualization_url'] = visualization_urls  # Добавление путей к графикам в результат

    return results


def analyze_seasonal_preferences(input: str) -> dict:
    """
    Анализ сезонных предпочтений по товарам
    Подсчёт объёма покупок и средней суммы по категориям в каждый сезон, выявление лидеров продаж

    Параметры:

    Возвращает:
        dict: словарь со всеми результатами анализа
    """

    # 1. Предобработка и проверка данных
    required_columns = ['Season', 'Category', 'Purchase Amount (USD)']
    for col in required_columns:
        if col not in df.columns:
            return {"error": f"В данных отсутствует обязательный столбец: {col}"}

    # Нормализация названий сезонов
    season_mapping = {
        'spring': 'Spring',
        'summer': 'Summer',
        'fall': 'Fall',
        'winter': 'Winter',
        'Spring': 'Spring',
        'Summer': 'Summer',
        'Fall': 'Fall',
        'Winter': 'Winter'
    }

    df['Season'] = df['Season'].astype(str).str.strip().str.lower().map(lambda x: season_mapping.get(x, x))

    # Оставляем только валидные сезоны
    valid_seasons = ['Spring', 'Summer', 'Fall', 'Winter']

    # 2. Базовая статистика: распределение покупок по сезонам
    seasonal_counts = df['Season'].value_counts().to_dict()
    total_purchases = len(df)

    # 3. Статистика покупок и средней суммы по сезонам и категориям
    seasonal_analysis = {}

    for season in valid_seasons:
        season_data = df[df['Season'] == season]

        # Общее число покупок в сезоне
        season_total = len(season_data)

        # Статистика по категориям
        category_stats = season_data.groupby('Category').agg({
            'Purchase Amount (USD)': ['count', 'mean', 'sum', 'std']
        }).round(2)

        # Переименование столбцов
        category_stats.columns = ['count', 'avg_amount', 'total_amount', 'std_amount']
        category_stats = category_stats.reset_index()

        # Преобразование в словарь
        category_dict = {}
        for _, row in category_stats.iterrows():
            category = row['Category']
            category_dict[category] = {
                'count': int(row['count']),
                'percentage': round(row['count'] / season_total * 100, 1),
                'avg_amount': float(row['avg_amount']),
                'total_amount': float(row['total_amount']),
                'std_amount': float(row['std_amount'])
            }

        # Лидеры продаж в сезоне (по объёму покупок)
        top_categories_by_count = category_stats.nlargest(3, 'count')[['Category', 'count']].to_dict('records')
        top_categories_by_revenue = category_stats.nlargest(3, 'total_amount')[['Category', 'total_amount']].to_dict('records')

        # Характеристика сезона
        season_summary = {
            'total_purchases': int(season_total),
            'percentage_of_total': round(season_total / total_purchases * 100, 1),
            'total_revenue': float(season_data['Purchase Amount (USD)'].sum()),
            'avg_transaction_value': float(season_data['Purchase Amount (USD)'].mean()),
            'top_categories_by_count': top_categories_by_count,
            'top_categories_by_revenue': top_categories_by_revenue,
            'category_details': category_dict
        }

        seasonal_analysis[season] = season_summary

    # 4. Анализ сезонных трендов (межсезонное сравнение)
    seasonal_trends = {}

    # Показатели каждой категории в разных сезонах
    all_categories = df['Category'].unique()

    for category in all_categories:
        category_data = df[df['Category'] == category]

        category_season_stats = []
        for season in valid_seasons:
            season_cat_data = category_data[category_data['Season'] == season]
            if len(season_cat_data) > 0:
                stats = {
                    'season': season,
                    'count': len(season_cat_data),
                    'avg_amount': float(season_cat_data['Purchase Amount (USD)'].mean()),
                    'total_amount': float(season_cat_data['Purchase Amount (USD)'].sum()),
                    'percentage': round(len(season_cat_data) / len(category_data) * 100, 1)
                }
                category_season_stats.append(stats)

        # Лучший сезон продаж для категории
        if category_season_stats:
            best_by_count = max(category_season_stats, key=lambda x: x['count'])
            best_by_revenue = max(category_season_stats, key=lambda x: x['total_amount'])

            seasonal_trends[category] = {
                'total_purchases': len(category_data),
                'seasonal_distribution': category_season_stats,
                'best_season_by_count': {
                    'season': best_by_count['season'],
                    'count': best_by_count['count'],
                    'percentage': best_by_count['percentage']
                },
                'best_season_by_revenue': {
                    'season': best_by_revenue['season'],
                    'total_amount': best_by_revenue['total_amount']
                },
                'seasonality_index': calculate_seasonality_index(category_season_stats)
            }

    # 5. Анализ сезонных пиков (категории с выраженной сезонностью)
    highly_seasonal_categories = []

    for category, trend in seasonal_trends.items():
        distribution = trend['seasonal_distribution']
        if len(distribution) >= 2:  # Данные минимум за два сезона
            counts = [d['count'] for d in distribution]
            max_count = max(counts)
            min_count = min(counts)

            if min_count > 0:  # Избегаем деления на ноль
                seasonality_ratio = max_count / min_count
                if seasonality_ratio >= 2.0:  # Выраженная сезонность (пиковый сезон в 2+ раза выше минимального)
                    highly_seasonal_categories.append({
                        'category': category,
                        'seasonality_ratio': round(seasonality_ratio, 2),
                        'peak_season': trend['best_season_by_count']['season'],
                        'peak_count': trend['best_season_by_count']['count']
                    })

    # Сортировка по коэффициенту сезонности
    highly_seasonal_categories.sort(key=lambda x: x['seasonality_ratio'], reverse=True)

    # 6. Межсезонное сравнение: общие данные
    cross_season_comparison = {}

    # Общие показатели по сезонам
    seasonal_performance = []
    for season in valid_seasons:
        if season in seasonal_analysis:
            season_data = seasonal_analysis[season]
            seasonal_performance.append({
                'season': season,
                'total_purchases': season_data['total_purchases'],
                'total_revenue': season_data['total_revenue'],
                'avg_transaction_value': season_data['avg_transaction_value'],
                'purchase_density': round(season_data['total_purchases'] / len(df[df['Season'] == season].index.unique()) if len(df[df['Season'] == season]) > 0 else 0, 2)
            })

    # Сезоны с максимальными и минимальными продажами
    if seasonal_performance:
        peak_season = max(seasonal_performance, key=lambda x: x['total_revenue'])
        low_season = min(seasonal_performance, key=lambda x: x['total_revenue'])

        cross_season_comparison = {
            'seasonal_performance': seasonal_performance,
            'peak_season': {
                'season': peak_season['season'],
                'total_revenue': peak_season['total_revenue'],
                'reason': analyze_peak_season_reason(seasonal_analysis[peak_season['season']])
            },
            'low_season': {
                'season': low_season['season'],
                'total_revenue': low_season['total_revenue']
            },
            'revenue_variation': round((peak_season['total_revenue'] - low_season['total_revenue']) / low_season['total_revenue'] * 100, 1) if low_season['total_revenue'] > 0 else 0
        }

    # 7. Сезонные маркетинговые рекомендации
    marketing_recommendations = generate_seasonal_recommendations(seasonal_analysis, seasonal_trends, highly_seasonal_categories)

    # 8. Сводка результатов
    results = {
        'basic_stats': {
            'total_purchases': int(total_purchases),
            'seasons_covered': valid_seasons,
            'purchases_by_season': seasonal_counts,
            'categories_analyzed': list(all_categories)
        },
        'seasonal_analysis': seasonal_analysis,
        'category_seasonal_trends': seasonal_trends,
        'highly_seasonal_categories': highly_seasonal_categories[:10],  # Возвращаем только топ-10
        'cross_season_comparison': cross_season_comparison,
        'marketing_recommendations': marketing_recommendations,
        'summary': {
            'peak_season': cross_season_comparison.get('peak_season', {}).get('season', 'Unknown'),
            'most_consistent_category': find_most_consistent_category(seasonal_trends),
            'most_seasonal_category': highly_seasonal_categories[0]['category'] if highly_seasonal_categories else 'None',
            'highest_avg_transaction_season': max(seasonal_performance, key=lambda x: x['avg_transaction_value'])['season'] if seasonal_performance else 'Unknown',
            'analysis_timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    }

    # Визуализации и сохранение путей в results
    visualization_urls = []
    figures_dir = os.path.join(work_path, '../out', 'figures')
    os.makedirs(figures_dir, exist_ok=True)

    try:
        # 1) Столбчатая диаграмма покупок по сезонам
        plt.figure(figsize=(8,5))
        seasons = valid_seasons
        counts = [seasonal_counts.get(s, 0) for s in seasons]
        plt.bar(seasons, counts, color=['#66c2a5','#fc8d62','#8da0cb','#e78ac3'])
        plt.title('Purchases by Season')
        plt.ylabel('Purchases')
        path1 = 'figures/purchases_by_season.png'
        plt.savefig(os.path.join(work_path, '../out', path1), bbox_inches='tight')
        plt.close()
        visualization_urls.append(path1)
    except Exception:
        pass

    try:
        # 2) Столбчатая диаграмма общей выручки по сезонам
        if seasonal_performance:
            plt.figure(figsize=(8,5))
            seasons_perf = [s['season'] for s in seasonal_performance]
            revenues = [s['total_revenue'] for s in seasonal_performance]
            plt.bar(seasons_perf, revenues, color='steelblue')
            plt.title('Total Revenue by Season')
            plt.ylabel('Total Revenue (USD)')
            path2 = 'figures/total_revenue_by_season.png'
            plt.savefig(os.path.join(work_path, '../out', path2), bbox_inches='tight')
            plt.close()
            visualization_urls.append(path2)
    except Exception:
        pass

    try:
        # 3) Горизонтальная диаграмма высокосезонных категорий (топ-10)
        if highly_seasonal_categories:
            top_seasonal = highly_seasonal_categories[:10]
            cats = [c['category'] for c in top_seasonal]
            ratios = [c['seasonality_ratio'] for c in top_seasonal]
            plt.figure(figsize=(10,5))
            plt.barh(cats[::-1], ratios[::-1], color='darkorange')
            plt.title('Top Highly Seasonal Categories (seasonality ratio)')
            plt.xlabel('Seasonality Ratio')
            path3 = 'figures/highly_seasonal_categories.png'
            plt.savefig(os.path.join(work_path, '../out', path3), bbox_inches='tight')
            plt.close()
            visualization_urls.append(path3)
    except Exception:
        pass

    try:
        # 4) Составная столбчатая диаграмма по сезонам для выборки категорий (топ-8 по частоте)
        sample_cats = list(seasonal_trends.keys())[:8]
        if sample_cats:
            matrix = {s: {season:0 for season in valid_seasons} for s in sample_cats}
            for cat in sample_cats:
                dist = seasonal_trends.get(cat, {}).get('seasonal_distribution', [])
                for d in dist:
                    season = d.get('season')
                    count = d.get('count', 0)
                    if season in valid_seasons:
                        matrix[cat][season] = count
            df_matrix = pd.DataFrame.from_dict(matrix, orient='index')[valid_seasons]
            plt.figure(figsize=(10,6))
            df_matrix.plot(kind='bar', stacked=True, figsize=(10,6), colormap='tab20')
            plt.title('Seasonal Distribution for Sample Categories')
            plt.xlabel('Category')
            plt.ylabel('Purchase Count')
            plt.xticks(rotation=45, ha='right')
            path4 = 'figures/sample_categories_seasonal_distribution.png'
            plt.savefig(os.path.join(work_path, '../out', path4), bbox_inches='tight')
            plt.close()
            visualization_urls.append(path4)
    except Exception:
        pass

    # Добавление путей к графикам в словарь результатов (относительные пути в out/)
    results['visualization_url'] = visualization_urls

    return results


def calculate_seasonality_index(seasonal_stats):
    """Расчёт индекса сезонности"""
    if not seasonal_stats:
        return 0

    counts = [s['count'] for s in seasonal_stats]
    avg_count = sum(counts) / len(counts)

    if avg_count == 0:
        return 0

    # Коэффициент вариации как индекс сезонности
    variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
    std_dev = variance ** 0.5
    seasonality_index = std_dev / avg_count if avg_count > 0 else 0

    return round(seasonality_index, 3)


def analyze_peak_season_reason(season_data):
    """Анализ причин пикового сезона"""
    top_categories = season_data['top_categories_by_count'][:2]
    reasons = []

    for cat in top_categories:
        category_name = cat['Category']
        category_details = season_data['category_details'].get(category_name, {})
        reasons.append(f"{category_name} ({cat['count']} покупок, {category_details.get('percentage', 0)}% от общего числа)")

    return f"Основные категории-вкладчики: {', '.join(reasons)}"


def analyze_monthly_trends():
    """Анализ месячных трендов (при наличии данных по месяцам)"""
    monthly_insights = {}

    # Попытка извлечь информацию о месяце из существующих столбцов
    month_col = None
    for col in df.columns:
        if col.lower() in ['month', 'purchase_month', 'order_month']:
            month_col = col
            break

    if month_col:
        monthly_stats = df.groupby(month_col).agg({
            'Purchase Amount (USD)': ['count', 'mean', 'sum']
        }).round(2)

        monthly_stats.columns = ['count', 'avg_amount', 'total_amount']
        monthly_stats = monthly_stats.reset_index()

        monthly_insights = monthly_stats.to_dict('records')

    return monthly_insights


def generate_seasonal_recommendations(seasonal_analysis, seasonal_trends, highly_seasonal_categories):
    """Формирование сезонных маркетинговых рекомендаций"""
    recommendations = []

    # 1. Рекомендации по управлению запасами
    for season, data in seasonal_analysis.items():
        top_categories = data['top_categories_by_count'][:3]
        if top_categories:
            categories_str = ', '.join([cat['Category'] for cat in top_categories])
            recommendations.append({
                'season': season,
                'type': 'Управление запасами',
                'recommendation': f"Увеличить запасы категорий {categories_str}",
                'reason': f"Самые популярные категории сезона, {sum(data['category_details'][cat['Category']]['percentage'] for cat in top_categories if cat['Category'] in data['category_details']):.1f}% от всех покупок"
            })

    # 2. Рекомендации по промоакциям
    for item in highly_seasonal_categories[:3]:
        recommendations.append({
            'category': item['category'],
            'type': 'Промоакции',
            'recommendation': f"Провести акцентную промоакцию в сезон {item['peak_season']}",
            'reason': f"Продажи этой категории в сезон {item['peak_season']} в {item['seasonality_ratio']:.1f} раз выше, чем в другие сезоны"
        })

    # 3. Рекомендации по ценообразованию
    for season, data in seasonal_analysis.items():
        if data['avg_transaction_value'] > 0:
            # Категории с высокой ценностью в сезоне
            high_value_categories = []
            for category, details in data['category_details'].items():
                if details['avg_amount'] > data['avg_transaction_value'] * 1.2:  # На 20% выше среднего
                    high_value_categories.append(category)

            if high_value_categories:
                recommendations.append({
                    'season': season,
                    'type': 'Ценообразование',
                    'recommendation': f"Применить премиальное ценообразование для категорий {', '.join(high_value_categories[:3])}",
                    'reason': f"Средняя стоимость сделки по этим категориям в сезоне выше (${data['avg_transaction_value']:.2f}+)"
                })

    return recommendations


def find_most_consistent_category(seasonal_trends):
    """Поиск наиболее стабильной категории (с минимальной сезонной вариативностью)"""
    if not seasonal_trends:
        return "None"

    most_consistent = None
    min_seasonality = float('inf')

    for category, trend in seasonal_trends.items():
        seasonality = trend.get('seasonality_index', 1.0)
        if seasonality < min_seasonality:
            min_seasonality = seasonality
            most_consistent = category

    return most_consistent


def analyze_review_rating_impact(input: str) -> dict:
    """
    Анализ связи оценок отзывов с расходами

    Параметры:

    Возвращает:
        dict: словарь с наиболее важными результатами анализа
    """

    # 1. Предобработка и проверка данных
    required_columns = ['Review Rating', 'Purchase Amount (USD)', 'Previous Purchases']
    for col in required_columns:
        if col not in df.columns:
            return {"error": f"В данных отсутствует обязательный столбец: {col}"}

    # Очистка данных
    df_clean = df.copy()
    df_clean['Review Rating'] = pd.to_numeric(df_clean['Review Rating'], errors='coerce')
    df_clean = df_clean.dropna(subset=['Review Rating'])
    df_clean = df_clean[(df_clean['Review Rating'] >= 1) & (df_clean['Review Rating'] <= 5)]

    if len(df_clean) == 0:
        return {"error": "После очистки не осталось валидных данных"}

    # 2. Ключевой результат: сравнение групп по оценкам
    # Создание упрощённых интервалов оценок
    def create_simple_rating_groups(rating):
        if rating >= 4.0:
            return 'High (4.0-5.0)'
        elif rating >= 3.0:
            return 'Medium (3.0-3.99)'
        else:
            return 'Low (1.0-2.99)'

    df_clean['Rating Group'] = df_clean['Review Rating'].apply(create_simple_rating_groups)

    # Анализ по группам оценок
    rating_group_analysis = {}
    for group in ['High (4.0-5.0)', 'Medium (3.0-3.99)', 'Low (1.0-2.99)']:
        if group in df_clean['Rating Group'].unique():
            group_data = df_clean[df_clean['Rating Group'] == group]
            rating_group_analysis[group] = {
                'customer_count': int(len(group_data)),
                'percentage': round(len(group_data) / len(df_clean) * 100, 1),
                'avg_purchase_amount': round(float(group_data['Purchase Amount (USD)'].mean()), 2),
                'avg_previous_purchases': round(float(group_data['Previous Purchases'].mean()), 1),
                'total_revenue': round(float(group_data['Purchase Amount (USD)'].sum()), 2)
            }

    # 3. Ключевой результат: корреляционный анализ
    correlation_results = {}
    if len(df_clean) >= 10:
        try:
            # Корреляция оценки и суммы покупки
            corr_amount, p_value_amount = pearsonr(
                df_clean['Review Rating'],
                df_clean['Purchase Amount (USD)']
            )

            # Корреляция оценки и числа предыдущих покупок
            corr_prev, p_value_prev = pearsonr(
                df_clean['Review Rating'],
                df_clean['Previous Purchases']
            )

            correlation_results = {
                'rating_vs_purchase_amount': {
                    'correlation': round(corr_amount, 3),
                    'p_value': round(p_value_amount, 4),
                    'significant': p_value_amount < 0.05,
                    'strength': 'сильная' if abs(corr_amount) >= 0.5 else 'умеренная' if abs(corr_amount) >= 0.3 else 'слабая'
                },
                'rating_vs_previous_purchases': {
                    'correlation': round(corr_prev, 3),
                    'p_value': round(p_value_prev, 4),
                    'significant': p_value_prev < 0.05
                }
            }
        except:
            correlation_results = {'error': 'Не удалось рассчитать корреляцию'}

    # 4. Ключевой результат: сравнение ключевых показателей
    # Различия между группами с максимальной и минимальной оценкой
    key_comparisons = {}
    if len(rating_group_analysis) >= 2:
        high_group = rating_group_analysis.get('High (4.0-5.0)', {})
        low_group = rating_group_analysis.get('Low (1.0-2.99)', {})

        if high_group and low_group:
            amount_diff = high_group['avg_purchase_amount'] - low_group['avg_purchase_amount']
            prev_diff = high_group['avg_previous_purchases'] - low_group['avg_previous_purchases']

            key_comparisons = {
                'high_vs_low_rating': {
                    'purchase_amount_difference': round(amount_diff, 2),
                    'purchase_amount_percentage_diff': round(amount_diff / low_group['avg_purchase_amount'] * 100, 1) if low_group['avg_purchase_amount'] > 0 else 0,
                    'previous_purchases_difference': round(prev_diff, 1),
                    'revenue_contribution_ratio': round(high_group['total_revenue'] / low_group['total_revenue'], 1) if low_group['total_revenue'] > 0 else 'N/A'
                }
            }

    # 5. Ключевой результат: бизнес-инсайты
    insights = []

    # Инсайт по распределению оценок
    high_rating_percentage = rating_group_analysis.get('High (4.0-5.0)', {}).get('percentage', 0)
    if high_rating_percentage > 50:
        insights.append("Более половины клиентов ставят высокие оценки (4.0+), что указывает на высокую общую удовлетворённость")
    elif high_rating_percentage < 30:
        insights.append("Доля клиентов с высокими оценками низкая — стоит обратить внимание на качество обслуживания")

    # Инсайт по различиям в расходах
    if key_comparisons and 'high_vs_low_rating' in key_comparisons:
        diff_info = key_comparisons['high_vs_low_rating']
        insights.append(f"Клиенты с высокими оценками тратят в среднем на ${diff_info['purchase_amount_difference']:.2f} больше, чем клиенты с низкими оценками ({diff_info['purchase_amount_percentage_diff']:.1f}%)")

    # Инсайт по корреляции
    if correlation_results and 'rating_vs_purchase_amount' in correlation_results:
        corr_info = correlation_results['rating_vs_purchase_amount']
        if corr_info['significant']:
            direction = "положительная" if corr_info['correlation'] > 0 else "отрицательная"
            insights.append(f"Между оценкой и суммой покупки есть {direction} связь ({corr_info['strength']} корреляция, r={corr_info['correlation']:.2f})")

    # 6. Объединение наиболее важных результатов
    results = {
        'overall_summary': {
            'total_customers': int(len(df_clean)),
            'avg_rating': round(float(df_clean['Review Rating'].mean()), 2),
            'avg_purchase_amount': round(float(df_clean['Purchase Amount (USD)'].mean()), 2),
            'avg_previous_purchases': round(float(df_clean['Previous Purchases'].mean()), 1)
        },
        'rating_distribution': {
            'high_rating_percentage': high_rating_percentage,
            'rating_groups_summary': {
                group: {
                    'customer_count': data['customer_count'],
                    'percentage': data['percentage']
                }
                for group, data in rating_group_analysis.items()
            }
        },
        'key_metrics_by_rating': {
            group: {
                'avg_purchase_amount': data['avg_purchase_amount'],
                'avg_previous_purchases': data['avg_previous_purchases'],
                'total_revenue': data['total_revenue']
            }
            for group, data in rating_group_analysis.items()
        },
        'correlation_analysis': correlation_results,
        'key_comparisons': key_comparisons,
        'top_insights': insights[:3] if insights else ["Недостаточно данных или явных закономерностей"],
        'analysis_timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Визуализации и сохранение путей в results
    visualization_urls = []
    figures_dir = os.path.join(work_path, '../out', 'figures')
    os.makedirs(figures_dir, exist_ok=True)

    try:
        # 1) Столбчатая диаграмма распределения оценок (High/Med/Low)
        groups = ['High (4.0-5.0)', 'Medium (3.0-3.99)', 'Low (1.0-2.99)']
        counts = [rating_group_analysis.get(g, {}).get('customer_count', 0) for g in groups]
        plt.figure(figsize=(7,4))
        plt.bar(groups, counts, color=['#4CAF50','#FFD54F','#EF5350'])
        plt.title('Rating Group Distribution')
        plt.ylabel('Customer Count')
        path1 = 'figures/rating_group_distribution.png'
        plt.savefig(os.path.join(work_path, '../out', path1), bbox_inches='tight')
        plt.close()
        visualization_urls.append(path1)
    except Exception:
        pass

    try:
        # 2) Столбчатая диаграмма средней суммы покупок по группам оценок
        avg_amounts = [rating_group_analysis.get(g, {}).get('avg_purchase_amount', 0) for g in groups]
        plt.figure(figsize=(7,4))
        plt.bar(groups, avg_amounts, color=['#2E7D32','#F9A825','#C62828'])
        plt.title('Average Purchase Amount by Rating Group')
        plt.ylabel('Average Purchase Amount (USD)')
        path2 = 'figures/avg_purchase_by_rating_group.png'
        plt.savefig(os.path.join(work_path, '../out', path2), bbox_inches='tight')
        plt.close()
        visualization_urls.append(path2)
    except Exception:
        pass

    try:
        # 3) Точечная диаграмма: оценка vs сумма покупки
        plt.figure(figsize=(7,5))
        plt.scatter(df_clean['Review Rating'], df_clean['Purchase Amount (USD)'], alpha=0.6, s=20)
        plt.xlabel('Review Rating')
        plt.ylabel('Purchase Amount (USD)')
        plt.title('Rating vs Purchase Amount')
        path3 = 'figures/rating_vs_purchase_scatter.png'
        plt.savefig(os.path.join(work_path, '../out', path3), bbox_inches='tight')
        plt.close()
        visualization_urls.append(path3)
    except Exception:
        pass

    try:
        # 4) Столбчатая диаграмма общей выручки по группам оценок
        totals = [rating_group_analysis.get(g, {}).get('total_revenue', 0) for g in groups]
        plt.figure(figsize=(7,4))
        plt.bar(groups, totals, color=['#66BB6A','#FFCA28','#EF5350'])
        plt.title('Total Revenue by Rating Group')
        plt.ylabel('Total Revenue (USD)')
        path4 = 'figures/total_revenue_by_rating_group.png'
        plt.savefig(os.path.join(work_path, '../out', path4), bbox_inches='tight')
        plt.close()
        visualization_urls.append(path4)
    except Exception:
        pass

    # Добавление путей к графикам в словарь результатов (относительные пути в out/)
    results['visualization_url'] = visualization_urls

    return results

def analyze_payment_method_impact(input: str) -> dict:
    """
    Анализ влияния способа оплаты на сумму покупки

    Параметры:

    Возвращает:
        dict: словарь с результатами анализа
    """

    # 1. Проверка данных
    required_columns = ['Payment Method', 'Purchase Amount (USD)']
    for col in required_columns:
        if col not in df.columns:
            return {"error": f"В данных отсутствует обязательный столбец: {col}"}

    # 2. Очистка данных
    df_clean = df.copy()
    df_clean['Payment Method'] = df_clean['Payment Method'].astype(str).str.strip()

    # Фильтрация невалидных данных
    df_clean = df_clean[df_clean['Purchase Amount (USD)'] > 0]

    if len(df_clean) == 0:
        return {"error": "После очистки не осталось валидных данных"}

    # 3. Базовый статистический анализ
    # Распределение способов оплаты
    payment_counts = df_clean['Payment Method'].value_counts().to_dict()
    total_transactions = len(df_clean)

    # Статистика по способам оплаты
    payment_stats = {}
    for method, group in df_clean.groupby('Payment Method'):
        payment_stats[method] = {
            'transaction_count': int(len(group)),
            'percentage': round(len(group) / total_transactions * 100, 1),
            'total_amount': round(float(group['Purchase Amount (USD)'].sum()), 2),
            'avg_amount': round(float(group['Purchase Amount (USD)'].mean()), 2),
            'median_amount': round(float(group['Purchase Amount (USD)'].median()), 2),
            'std_amount': round(float(group['Purchase Amount (USD)'].std()), 2),
            'min_amount': round(float(group['Purchase Amount (USD)'].min()), 2),
            'max_amount': round(float(group['Purchase Amount (USD)'].max()), 2)
        }

    # 4. Ключевое сравнение: максимальная и минимальная средняя сумма
    avg_amounts = {method: stats['avg_amount'] for method, stats in payment_stats.items()}
    if avg_amounts:
        max_avg_method = max(avg_amounts, key=avg_amounts.get)
        min_avg_method = min(avg_amounts, key=avg_amounts.get)

        key_comparisons = {
            'highest_avg_payment': {
                'method': max_avg_method,
                'amount': avg_amounts[max_avg_method],
                'details': payment_stats[max_avg_method]
            },
            'lowest_avg_payment': {
                'method': min_avg_method,
                'amount': avg_amounts[min_avg_method],
                'details': payment_stats[min_avg_method]
            },
            'difference': {
                'amount_diff': round(avg_amounts[max_avg_method] - avg_amounts[min_avg_method], 2),
                'percentage_diff': round((avg_amounts[max_avg_method] - avg_amounts[min_avg_method]) / avg_amounts[min_avg_method] * 100, 1) if avg_amounts[min_avg_method] > 0 else 0
            }
        }
    else:
        key_comparisons = {}

    # 5. Статистический анализ: ANOVA
    anova_results = {}
    if len(payment_stats) >= 2:
        try:
            # Подготовка данных по группам
            groups = []
            for method in payment_stats.keys():
                group_data = df_clean[df_clean['Payment Method'] == method]['Purchase Amount (USD)'].values
                if len(group_data) >= 2:  # Минимум 2 наблюдения
                    groups.append(group_data)

            if len(groups) >= 2:
                # Проведение ANOVA
                f_stat, p_value = f_oneway(*groups)

                anova_results = {
                    'f_statistic': round(f_stat, 4),
                    'p_value': round(p_value, 6),
                    'significant': p_value < 0.05,
                    'interpretation': 'Суммы покупок по разным способам оплаты статистически значимо различаются' if p_value < 0.05 else 'Суммы покупок по разным способам оплаты статистически значимо не различаются'
                }
        except Exception as e:
            anova_results = {'error': f'Ошибка ANOVA: {str(e)}'}

    # 6. Сравнение доли рынка и вклада в выручку
    contribution_analysis = {}
    for method, stats in payment_stats.items():
        contribution_analysis[method] = {
            'transaction_share': stats['percentage'],
            'revenue_share': round(stats['total_amount'] / df_clean['Purchase Amount (USD)'].sum() * 100, 1),
            'avg_transaction_value': stats['avg_amount']
        }

    # 7. Бизнес-инсайты
    insights = []

    # Инсайт по предпочтениям способов оплаты
    max_transactions = max(payment_counts.values())
    most_popular = [m for m, c in payment_counts.items() if c == max_transactions][0]
    insights.append(f"Самый популярный способ оплаты: {most_popular} ({payment_counts[most_popular]} транзакций)")

    # Инсайт по различиям в суммах
    if key_comparisons:
        diff = key_comparisons['difference']
        insights.append(f"Средняя сумма по {key_comparisons['highest_avg_payment']['method']} на {diff['percentage_diff']:.1f}% выше, чем по {key_comparisons['lowest_avg_payment']['method']}")

    # Инсайт по статистической значимости
    if anova_results and 'significant' in anova_results:
        if anova_results['significant']:
            insights.append("Суммы покупок по разным способам оплаты статистически значимо различаются")
        else:
            insights.append("Суммы покупок по разным способам оплаты статистически значимо не различаются")

    # Выявление высокоценных способов оплаты
    for method, contrib in contribution_analysis.items():
        if contrib['revenue_share'] > contrib['transaction_share'] + 10:  # Доля выручки заметно выше доли транзакций
            insights.append(f"{method} — высокоценный способ оплаты: {contrib['revenue_share']}% выручки при {contrib['transaction_share']}% транзакций")

    # 8. Объединение результатов
    results = {
        'overall_summary': {
            'total_transactions': total_transactions,
            'total_revenue': round(float(df_clean['Purchase Amount (USD)'].sum()), 2),
            'avg_transaction_value': round(float(df_clean['Purchase Amount (USD)'].mean()), 2),
            'unique_payment_methods': len(payment_stats)
        },
        'payment_method_distribution': {
            'transaction_counts': payment_counts,
            'percentage_breakdown': {method: stats['percentage'] for method, stats in payment_stats.items()}
        },
        'performance_by_payment_method': payment_stats,
        'contribution_analysis': contribution_analysis,
        'key_comparisons': key_comparisons,
        'statistical_analysis': anova_results,
        'business_insights': insights[:5]
    }

    # Визуализации и сохранение путей в results
    visualization_urls = []
    figures_dir = os.path.join(work_path, '../out', 'figures')
    os.makedirs(figures_dir, exist_ok=True)

    try:
        # 1) Столбчатая диаграмма числа транзакций по способам оплаты
        plt.figure(figsize=(8,5))
        methods = list(payment_counts.keys())
        counts = [payment_counts[m] for m in methods]
        plt.bar(methods, counts, color='skyblue')
        plt.title('Transaction Counts by Payment Method')
        plt.xlabel('Payment Method')
        plt.ylabel('Transaction Count')
        plt.xticks(rotation=45, ha='right')
        path_a = 'figures/payment_method_transaction_counts.png'
        plt.savefig(os.path.join(work_path, '../out', path_a), bbox_inches='tight')
        plt.close()
        visualization_urls.append(path_a)
    except Exception:
        pass

    try:
        # 2) Круговая диаграмма долей способов оплаты
        plt.figure(figsize=(6,6))
        series_counts = pd.Series(payment_counts)
        series_counts = series_counts.sort_values(ascending=False)
        series_counts.plot(kind='pie', autopct='%1.1f%%', startangle=90, pctdistance=0.75)
        plt.ylabel('')
        plt.title('Payment Method Share')
        path_b = 'figures/payment_method_share_pie.png'
        plt.savefig(os.path.join(work_path, '../out', path_b), bbox_inches='tight')
        plt.close()
        visualization_urls.append(path_b)
    except Exception:
        pass

    try:
        # 3) Столбчатая диаграмма средней суммы транзакции по способам оплаты
        plt.figure(figsize=(8,5))
        methods_avg = list(avg_amounts.keys()) if 'avg_amounts' in locals() else list(payment_stats.keys())
        avg_vals = [payment_stats[m]['avg_amount'] if m in payment_stats else 0 for m in methods_avg]
        plt.bar(methods_avg, avg_vals, color='seagreen')
        plt.title('Average Transaction Value by Payment Method')
        plt.xlabel('Payment Method')
        plt.ylabel('Average Amount (USD)')
        plt.xticks(rotation=45, ha='right')
        path_c = 'figures/avg_transaction_value_by_payment_method.png'
        plt.savefig(os.path.join(work_path, '../out', path_c), bbox_inches='tight')
        plt.close()
        visualization_urls.append(path_c)
    except Exception:
        pass

    try:
        # 4) Ящичковая диаграмма распределения сумм по способам оплаты (при достаточном объёме выборки)
        grouped = []
        labels = []
        for method in payment_stats.keys():
            vals = df_clean[df_clean['Payment Method'] == method]['Purchase Amount (USD)'].dropna().values
            if len(vals) >= 3:
                grouped.append(vals)
                labels.append(method)
        if grouped:
            plt.figure(figsize=(10,6))
            plt.boxplot(grouped, tick_labels=labels, vert=True, patch_artist=True)
            plt.title('Purchase Amount Distribution by Payment Method')
            plt.ylabel('Purchase Amount (USD)')
            plt.xticks(rotation=45, ha='right')
            path_d = 'figures/purchase_amount_boxplot_by_payment_method.png'
            plt.savefig(os.path.join(work_path, '../out', path_d), bbox_inches='tight')
            plt.close()
            visualization_urls.append(path_d)
    except Exception:
        pass

    # Добавление путей к графикам в словарь результатов (относительные пути в out/)
    results['visualization_url'] = visualization_urls

    return results

def create_data_analysis_registry():
    """Создание реестра инструментов анализа данных"""
    tool_registry = ToolRegistry()

    # Регистрация инструментов анализа данных
    tool_registry.register_function(
        name="Gender Preference Analysis",
        func=analyze_gender_preferences,
        description="Анализ покупательских предпочтений по полу, включая сумму расходов и предпочтения по категориям товаров."
    )

    tool_registry.register_function(
        name="Age Preference Analysis",
        func=analyze_age_preferences,
        description="Анализ покупательских предпочтений по возрастным группам, включая сумму расходов и предпочтения по категориям товаров."
    )

    tool_registry.register_function(
        name="Spending Differences Analysis",
        func=analyze_spending_differences,
        description="Анализ различий в расходах по полу и возрастным группам в разрезе категорий товаров."
    )

    tool_registry.register_function(
        name="Subscription Impact Analysis",
        func=analyze_subscription_impact,
        description="Анализ влияния статуса подписки на поведение покупок и сумму расходов."
    )

    tool_registry.register_function(
        name="Seasonal Preference Analysis",
        func=analyze_seasonal_preferences,
        description="Анализ сезонных предпочтений по товарам, выявление лидеров продаж в каждый сезон."
    )

    tool_registry.register_function(
        name="Review Rating Impact Analysis",
        func=analyze_review_rating_impact,
        description="Анализ влияния оценок отзывов на сумму покупок и частоту покупок."
    )

    tool_registry.register_function(
        name="Payment Method Impact Analysis",
        func=analyze_payment_method_impact,
        description="Анализ влияния способа оплаты на сумму покупок."
    )

    return tool_registry

if __name__ == "__main__":
    registry = create_data_analysis_registry()
    result = registry.execute_tool("Payment Method Impact Analysis", input_text=None)
    print(f"\nРезультат анализа: {result}")
