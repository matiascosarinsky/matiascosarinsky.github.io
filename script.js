const publicationsRoot = document.querySelector("#publications");
const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const renderLink = (link) => {
  if (!link?.url || !link?.label) return "";
  return `<a href="${escapeHtml(link.url)}" target="_blank" rel="noreferrer">${escapeHtml(link.label)}</a>`;
};

const renderAuthors = (authors, equalContributors = []) => authors.map((author) => {
  const marked = equalContributors.some((name) => name.toLowerCase() === author.toLowerCase());
  const rendered = author.toLowerCase() === "matias cosarinsky"
    ? `<strong>${escapeHtml(author)}</strong>`
    : escapeHtml(author);
  return `${rendered}${marked ? "*" : ""}`;
}).join(", ");

const renderVenue = (publication) => {
  const venue = String(publication.venue || "");
  const normalized = venue.toLowerCase().includes("arxiv") ? "arXiv" : venue;
  return [normalized, publication.year].filter(Boolean).join(", ");
};

const paperLink = (publication) => publication.links.find((link) => link.label.toLowerCase() === "paper")?.url;

const loadJson = (path) => fetch(path).then((response) => {
  if (!response.ok) throw new Error(`Could not load ${path}`);
  return response.json();
});

Promise.all([loadJson("data/publications.json"), loadJson("assets/publication-links.json")])
  .then(([publications, manualLinks]) => {
    const linkFields = [
      ["project_page", "Project Page"],
      ["paper", "Paper"],
      ["code", "Code"],
      ["dataset", "Dataset"],
      ["demo", "Demo"],
    ];
    publications = publications.map((publication) => {
      const config = manualLinks[publication.title];
      if (!config) return publication;
      const links = linkFields
        .filter(([field]) => config[field])
        .map(([field, label]) => ({label, url: config[field]}));
      return {...publication, figure: publication.figure || "", links};
    });
    publications.sort((a, b) => Number(b.year || 0) - Number(a.year || 0));
    if (!publications.length) {
      publicationsRoot.innerHTML = '<p class="empty">Publications coming soon.</p>';
      return;
    }

    const renderFigure = (publication) => {
      if (!publication.figure) return "";
      const source = escapeHtml(publication.figure);
      const alt = `Figure 1 from ${escapeHtml(publication.title)}`;
      return `<img class="publication-figure" src="${source}" alt="${alt}" loading="lazy">`;
    };

    publicationsRoot.innerHTML = publications.map((publication) => `
      <article class="publication${publication.figure ? " has-figure" : ""}">
        ${renderFigure(publication)}
        <div>
          <h3 class="publication-title">
            ${paperLink(publication)
              ? `<a class="publication-title-link" href="${escapeHtml(paperLink(publication))}" target="_blank" rel="noreferrer">${escapeHtml(publication.title)}</a>`
              : escapeHtml(publication.title)}
          </h3>
          <p class="publication-authors">${renderAuthors(publication.authors, publication.equal_contributors)}</p>
          <p class="publication-venue">${escapeHtml(renderVenue(publication))}</p>
          <div class="publication-links">${publication.links.map(renderLink).join("")}</div>
        </div>
      </article>
    `).join("");
  })
  .catch(() => {
    publicationsRoot.innerHTML = '<p class="empty">Publication list temporarily unavailable.</p>';
  });
