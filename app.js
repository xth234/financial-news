const NEWS_URL = "data/news.json";
let allNews = [];
const CAT_ICONS = { "AI": "🧠", "区块链": "⛓", "黄金": "🥇", "机器人": "🤖", "地缘": "🌍", "美债": "🏦", "科技股": "📊" };

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
    document.getElementById("totalCount").textContent = allNews.length;
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
    .map((item) => {
      const catTags = (item.categories || [])
        .map((c) => `<span class="cat-tag">${CAT_ICONS[c] || ""} ${c}</span>`)
        .join("");
      const snippet = (item.content || item.summary || "").replace(/<[^>]+>/g, "").slice(0, 150);
      return `
    <article class="news-card">
      <div class="meta">
        <span class="source-badge lang-${item.lang}">${item.source}</span>
        <span class="time">${new Date(item.published).toLocaleString("zh-CN")}</span>
      </div>
      <h2><a href="article.html?id=${item.id}">${item.title}</a></h2>
      <div class="summary">${snippet}...</div>
      <div class="cat-tags">${catTags}</div>
    </article>`;
    })
    .join("");
}

function filter() {
  const lang = (document.querySelector("#langTabs .active") || {}).dataset?.lang || "all";
  const cat = (document.querySelector("#catTabs .active") || {}).dataset?.cat || "all";
  const keyword = document.getElementById("searchBox").value.trim().toLowerCase();
  let filtered = allNews;
  if (lang !== "all") filtered = filtered.filter((n) => n.lang === lang);
  if (cat !== "all") filtered = filtered.filter((n) => (n.categories || []).includes(cat));
  if (keyword) {
    filtered = filtered.filter(
      (n) =>
        n.title.toLowerCase().includes(keyword) ||
        (n.content || "").toLowerCase().includes(keyword)
    );
  }
  render(filtered);
}

document.querySelectorAll("#langTabs .tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#langTabs .tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    filter();
  });
});

document.querySelectorAll("#catTabs .tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#catTabs .tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    filter();
  });
});

document.getElementById("searchBox").addEventListener("input", filter);

loadNews();
setInterval(loadNews, 60000);
