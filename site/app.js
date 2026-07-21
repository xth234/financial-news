const NEWS_URL = "data/news.json";
let allNews = [];

async function loadNews() {
  const container = document.getElementById("newsContainer");
  try {
    const res = await fetch(NEWS_URL + "?t=" + Date.now());
    if (!res.ok) throw new Error("HTTP " + res.status);
    allNews = await res.json();
    render(allNews);
    const times = allNews.map((n) => n.published).filter(Boolean).sort().reverse();
    if (times.length) {
      document.getElementById("updateTime").textContent =
        new Date(times[0]).toLocaleString("zh-CN");
    }
  } catch (e) {
    container.innerHTML = `<div class="loading">\u52a0\u8f7d\u5931\u8d25\uff1a${e.message}</div>`;
  }
}

function render(news) {
  const container = document.getElementById("newsContainer");
  if (!news.length) {
    container.innerHTML = '<div class="loading">\u6682\u65e0\u65b0\u95fb</div>';
    return;
  }
  container.innerHTML = news
    .map(
      (item) => `
    <article class="news-card">
      <div class="meta">
        <span class="source-badge lang-${item.lang}">${item.source}</span>
        <span class="time">${new Date(item.published).toLocaleString("zh-CN")}</span>
      </div>
      <h2><a href="${item.link}" target="_blank" rel="noopener">${item.title}</a></h2>
      <div class="summary">${item.summary || ""}</div>
    </article>`
    )
    .join("");
}

function filter() {
  const lang = document.querySelector(".tab.active").dataset.lang;
  const keyword = document.getElementById("searchBox").value.trim().toLowerCase();
  let filtered = allNews;
  if (lang !== "all") {
    filtered = filtered.filter((n) => n.lang === lang);
  }
  if (keyword) {
    filtered = filtered.filter(
      (n) =>
        n.title.toLowerCase().includes(keyword) ||
        n.summary.toLowerCase().includes(keyword)
    );
  }
  render(filtered);
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    filter();
  });
});

document.getElementById("searchBox").addEventListener("input", filter);

loadNews();
