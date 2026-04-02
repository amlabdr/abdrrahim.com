async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return response.json();
}

function renderHighlights(highlights) {
  const container = document.getElementById("highlights");
  container.innerHTML = "";

  highlights.forEach((item) => {
    const card = document.createElement("div");
    card.className = "stat-card";

    const value = document.createElement("strong");
    value.textContent = item.value;

    const label = document.createElement("span");
    label.textContent = item.label;

    card.append(value, label);
    container.appendChild(card);
  });
}

function renderTags(containerId, items) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  items.forEach((item) => {
    const tag = document.createElement("span");
    tag.className = "tag";
    tag.textContent = item;
    container.appendChild(tag);
  });
}

function renderSimpleList(containerId, items) {
  const container = document.getElementById(containerId);
  container.innerHTML = "";
  items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    container.appendChild(li);
  });
}

function renderTimeline(containerId, items) {
  const container = document.getElementById(containerId);
  const template = document.getElementById("timeline-item-template");
  container.innerHTML = "";

  items.forEach((item) => {
    const node = template.content.firstElementChild.cloneNode(true);
    node.querySelector(".timeline-title").textContent = item.title;
    node.querySelector(".timeline-subtitle").textContent = item.subtitle;
    node.querySelector(".timeline-date").textContent = item.date;

    const list = node.querySelector(".bullet-list");
    list.innerHTML = "";

    (item.points || []).forEach((point) => {
      const li = document.createElement("li");
      li.textContent = point;
      list.appendChild(li);
    });

    if (!item.points || item.points.length === 0) {
      list.remove();
    }

    container.appendChild(node);
  });
}

function renderSkills(groups) {
  const container = document.getElementById("skill-groups");
  container.innerHTML = "";

  groups.forEach((group) => {
    const article = document.createElement("article");
    article.className = "skill-group";

    const title = document.createElement("h3");
    title.textContent = group.title;

    const tags = document.createElement("div");
    tags.className = "tag-list";

    group.items.forEach((item) => {
      const tag = document.createElement("span");
      tag.className = "tag";
      tag.textContent = item;
      tags.appendChild(tag);
    });

    article.append(title, tags);
    container.appendChild(article);
  });
}

function renderContacts(contacts) {
  const container = document.getElementById("contact-list");
  container.innerHTML = "";

  contacts.forEach((item) => {
    const link = document.createElement("a");
    link.href = item.href;
    link.target = item.external ? "_blank" : "_self";
    if (item.external) {
      link.rel = "noreferrer";
    }
    link.textContent = item.label;
    container.appendChild(link);
  });
}

function formatPublicationDate(value) {
  if (!value) {
    return "Date unavailable";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(date);
}

function renderPublications(publications) {
  const container = document.getElementById("recent-publications");
  const template = document.getElementById("publication-template");
  container.innerHTML = "";

  publications.slice(0, 3).forEach((item) => {
    const node = template.content.firstElementChild.cloneNode(true);
    node.querySelector(".publication-date").textContent = formatPublicationDate(item.published);
    node.querySelector("h3").textContent = item.title;
    node.querySelector(".publication-source").textContent =
      [item.venue, item.authors].filter(Boolean).join(" | ");

    const linkBox = node.querySelector(".publication-links");
    linkBox.innerHTML = "";

    (item.links || []).forEach((linkItem) => {
      const link = document.createElement("a");
      link.href = linkItem.href;
      link.textContent = linkItem.label;
      link.target = "_blank";
      link.rel = "noreferrer";
      linkBox.appendChild(link);
    });

    container.appendChild(node);
  });

  const meta = document.getElementById("publication-meta");
  meta.textContent = publications.length > 0
    ? `Showing the 3 most recent from ${publications.length} loaded items`
    : "No publications loaded yet";
}

function renderSelectedPublications(publications) {
  const container = document.getElementById("selected-publications");
  const template = document.getElementById("publication-template");
  container.innerHTML = "";

  const selected = [...publications]
    .sort((left, right) => {
      const citationDelta = (right.citationCount || 0) - (left.citationCount || 0);
      if (citationDelta !== 0) {
        return citationDelta;
      }
      return (right.published || "").localeCompare(left.published || "");
    })
    .slice(0, 3);

  selected.forEach((item) => {
    const node = template.content.firstElementChild.cloneNode(true);
    node.querySelector(".publication-date").textContent = item.citationCount
      ? `${item.citationCount} citations`
      : formatPublicationDate(item.published);
    node.querySelector("h3").textContent = item.title;
    node.querySelector(".publication-source").textContent =
      [item.venue, item.authors].filter(Boolean).join(" | ");

    const linkBox = node.querySelector(".publication-links");
    linkBox.innerHTML = "";

    (item.links || []).forEach((linkItem) => {
      const link = document.createElement("a");
      link.href = linkItem.href;
      link.textContent = linkItem.label;
      link.target = "_blank";
      link.rel = "noreferrer";
      linkBox.appendChild(link);
    });

    container.appendChild(node);
  });
}

function applyProfile(profile) {
  document.title = `${profile.name} | ${profile.role}`;
  document.getElementById("hero-role").textContent = profile.role;
  document.getElementById("hero-name").textContent = profile.name;
  document.getElementById("hero-summary").textContent = profile.summary;
  document.getElementById("about-text").textContent = profile.about;
  document.getElementById("scholar-link").href = profile.links.scholar.href;
  document.getElementById("email-link").href = `mailto:${profile.workEmail}`;

  const heroCover = document.getElementById("hero-cover");
  const heroCoverImage = document.getElementById("hero-cover-image");
  if (profile.photo && profile.photo.src) {
    heroCoverImage.src = profile.photo.src;
    heroCoverImage.alt = profile.photo.alt || `Cover photo of ${profile.name}`;
    heroCover.hidden = false;
  }

  renderHighlights(profile.highlights);
  renderTags("focus-areas", profile.focusAreas);
  renderSimpleList("current-focus", profile.currentFocus);
  renderTimeline("experience-list", profile.experience);
  renderTimeline("education-list", profile.education);
  renderTimeline("leadership-list", profile.leadership);
  renderSkills(profile.skills);
  renderContacts([
    { label: profile.workEmail, href: `mailto:${profile.workEmail}`, external: false },
    { label: profile.location, href: "#top", external: false },
    profile.links.github,
    profile.links.linkedin,
    profile.links.scholar,
    profile.links.nist,
    profile.links.orcid
  ]);
}

async function init() {
  try {
    const [profile, publicationsFile] = await Promise.all([
      loadJson("data/profile.json"),
      loadJson("data/publications.json")
    ]);

    applyProfile(profile);
    renderPublications(publicationsFile.publications || []);
    renderSelectedPublications(publicationsFile.publications || []);
  } catch (error) {
    document.getElementById("publication-meta").textContent = "Site data failed to load";
    console.error(error);
  }
}

init();
