type HeaderProps = {
  documentCount: number;
  runCount: number;
  latestScore?: number;
};

function Header({ documentCount, runCount, latestScore }: HeaderProps) {
  return (
    <header className="hero">
      <div className="hero__copy">
        <p className="hero__eyebrow">Atlas NLP Research Radar</p>
        <h1>Track recent NLP research topics with multi-agent retrieval, synthesis, and critique.</h1>
        <p className="hero__description">
          Planner, Researcher, Critic, and Writer agents work across scholarly paper APIs and your
          own uploaded documents to explain what is happening now in NLP.
        </p>
      </div>
      <div className="hero__stats">
        <div className="metric-tile">
          <span>Indexed Documents</span>
          <strong>{documentCount}</strong>
        </div>
        <div className="metric-tile">
          <span>Recent Runs</span>
          <strong>{runCount}</strong>
        </div>
        <div className="metric-tile">
          <span>Latest Score</span>
          <strong>{latestScore !== undefined ? `${Math.round(latestScore * 100)}%` : "n/a"}</strong>
        </div>
      </div>
    </header>
  );
}

export default Header;
