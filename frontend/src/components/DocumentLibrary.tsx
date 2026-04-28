import SectionCard from "./SectionCard";
import type { DocumentRecord } from "../types/api";
import { formatDate } from "../utils/format";

type DocumentLibraryProps = {
  documents: DocumentRecord[];
};

function DocumentLibrary({ documents }: DocumentLibraryProps) {
  return (
    <SectionCard eyebrow="Documents" title="Indexed library">
      <div className="list-stack">
        {documents.length === 0 ? (
          <p className="muted-copy">Upload a file to seed the local retrieval index.</p>
        ) : (
          documents.map((document) => (
            <article key={document.document_id} className="list-row">
              <div>
                <strong>{document.filename}</strong>
                <p>
                  {document.chunk_count} chunks • {document.content_type}
                </p>
              </div>
              <time>{formatDate(document.uploaded_at)}</time>
            </article>
          ))
        )}
      </div>
    </SectionCard>
  );
}

export default DocumentLibrary;

