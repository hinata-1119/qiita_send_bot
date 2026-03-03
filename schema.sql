-- 1. ベクトル機能を有効化（既に行っていればスキップされます）
create extension if not exists vector;

-- 2. テーブルの定義（3072次元で確定）
-- すでにテーブルがある場合は、一度 drop table technical_articles; してから実行してください
create table if not exists technical_articles (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  url text unique not null,
  content text,
  source_tag text,
  embedding vector(3072), -- ここを3072に固定！
  created_at timestamp with time zone default now()
);

-- 3. 検索用関数の定義（match_articles）
-- 紹介された match_documents の機能を 3072次元用に調整したものです
create or replace function match_articles (
  query_embedding vector(3072),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  title text,
  url text,
  content text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    technical_articles.id,
    technical_articles.title,
    technical_articles.url,
    technical_articles.content,
    1 - (technical_articles.embedding <=> query_embedding) as similarity
  from technical_articles
  where 1 - (technical_articles.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
end;
$$;
