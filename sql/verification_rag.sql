SELECT COUNT(*) AS total_documents, COUNT(embedding) AS embedded_documents
FROM building_documents;

SELECT document_type, COUNT(*) AS document_count
FROM building_documents
GROUP BY document_type
ORDER BY document_type;
