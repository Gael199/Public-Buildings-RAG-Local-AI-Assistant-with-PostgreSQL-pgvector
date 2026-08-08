-- Vérifier le nombre de documents
SELECT
    COUNT(*) AS total_documents,
    COUNT(*) FILTER (WHERE document_type = 'building') AS building_documents,
    COUNT(*) FILTER (WHERE document_type = 'project') AS project_documents,
    COUNT(embedding) AS embedded_documents
FROM building_documents;

-- Vérifier les dimensions
SELECT
    MIN(vector_dims(embedding)) AS min_dimensions,
    MAX(vector_dims(embedding)) AS max_dimensions
FROM building_documents
WHERE embedding IS NOT NULL;

-- Aperçu des documents
SELECT
    document_id,
    document_type,
    building_id,
    project_id,
    title,
    LEFT(content, 250) AS content_preview,
    metadata
FROM building_documents
ORDER BY document_id
LIMIT 10;

-- Vérifier l'index HNSW
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'building_documents'
ORDER BY indexname;
