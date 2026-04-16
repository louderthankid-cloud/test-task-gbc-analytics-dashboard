CREATE TABLE orders (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    crm_id BIGINT UNIQUE NOT NULL,
    total_sum NUMERIC,
    city VARCHAR(255),
    utm_source VARCHAR(255),
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_data JSONB
);

ALTER TABLE orders DISABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION get_dashboard_metrics()
RETURNS json AS $$
DECLARE
    result json;
BEGIN
    SELECT json_build_object(
        'total_revenue', COALESCE((SELECT SUM(total_sum) FROM orders), 0),
        'orders_count', (SELECT COUNT(*) FROM orders),
        'avg_check', COALESCE((SELECT AVG(total_sum) FROM orders), 0),
        
        -- Группируем по городам
        'city_data', (
            SELECT COALESCE(json_agg(json_build_object('name', COALESCE(city, 'Не указан'), 'value', val)), '[]'::json)
            FROM (SELECT city, SUM(total_sum) as val FROM orders GROUP BY city ORDER BY val DESC) c
        ),
        
        -- Группируем по UTM
        'utm_data', (
            SELECT COALESCE(json_agg(json_build_object('name', COALESCE(utm_source, 'direct'), 'value', val)), '[]'::json)
            FROM (SELECT utm_source, SUM(total_sum) as val FROM orders GROUP BY utm_source ORDER BY val DESC) u
        ),
        
        -- Распаковываем JSON товаров и считаем 
        'top_products', (
            SELECT COALESCE(json_agg(json_build_object('name', p_name, 'value', qty)), '[]'::json)
            FROM (
                SELECT 
                    COALESCE(item->'offer'->>'name', item->>'productName', 'Неизвестно') as p_name,
                    SUM(CAST(item->>'quantity' AS numeric)) as qty
                FROM orders,
                jsonb_array_elements(
                    CASE 
                        WHEN jsonb_typeof(raw_data->'items') = 'array' THEN raw_data->'items' 
                        ELSE '[]'::jsonb 
                    END
                ) as item
                GROUP BY p_name
                ORDER BY qty DESC
                LIMIT 5
            ) p
        )
    ) INTO result;
    RETURN result;
END;
$$ LANGUAGE plpgsql;