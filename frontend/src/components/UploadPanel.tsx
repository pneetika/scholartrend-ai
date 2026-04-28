import SectionCard from "./SectionCard";

type UploadPanelProps = {
  isUploading: boolean;
  onUpload: (file: File) => Promise<void>;
};

function UploadPanel({ isUploading, onUpload }: UploadPanelProps) {
  const handleChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    await onUpload(file);
    event.target.value = "";
  };

  return (
    <SectionCard eyebrow="Knowledge Base" title="Upload source material">
      <label className="upload-dropzone">
        <input type="file" accept=".txt,.md,.json,.csv,.pdf" onChange={handleChange} />
        <strong>{isUploading ? "Uploading..." : "Drop a file or browse"}</strong>
        <span>Supports TXT, Markdown, JSON, CSV, and PDF uploads for local retrieval.</span>
      </label>
    </SectionCard>
  );
}

export default UploadPanel;

