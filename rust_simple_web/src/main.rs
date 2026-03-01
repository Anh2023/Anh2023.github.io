use axum::{response::Html, routing::get, Router};
use tokio::net::TcpListener;

/// 功能: 启动 HTTP 服务并注册首页路由。
/// 输入: 无。
/// 输出: 启动成功后持续监听 127.0.0.1:3000，失败时返回错误。
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 服务监听地址，浏览器访问该地址即可看到页面。
    let addr = "127.0.0.1:3000";
    let app = Router::new().route("/", get(home_page));
    let listener = TcpListener::bind(addr).await?;

    println!("服务已启动: http://{addr}");
    axum::serve(listener, app).await?;
    Ok(())
}

/// 功能: 返回首页 HTML 内容。
/// 输入: 无。
/// 输出: 一个带基础样式的网页。
async fn home_page() -> Html<&'static str> {
    Html(
        r#"<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Rust 简单网页</title>
  <style>
    :root {
      --bg-start: #f2efe8;
      --bg-end: #d9e2ec;
      --ink: #243447;
      --accent: #e4572e;
      --card: rgba(255, 255, 255, 0.78);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, var(--bg-start), var(--bg-end));
      color: var(--ink);
      font-family: "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
    }
    .card {
      width: min(680px, 92vw);
      border-radius: 22px;
      padding: 28px;
      background: var(--card);
      border: 1px solid rgba(255, 255, 255, 0.85);
      box-shadow: 0 18px 40px rgba(36, 52, 71, 0.16);
      animation: slide-in 680ms ease-out;
      backdrop-filter: blur(4px);
    }
    h1 { margin: 0 0 12px; font-size: clamp(1.6rem, 3.8vw, 2.3rem); }
    p { margin: 8px 0; line-height: 1.7; }
    .badge {
      display: inline-block;
      margin-top: 14px;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--accent);
      color: #fff;
      font-size: 0.9rem;
      letter-spacing: 0.02em;
    }
    @keyframes slide-in {
      from { opacity: 0; transform: translateY(14px); }
      to { opacity: 1; transform: translateY(0); }
    }
  </style>
</head>
<body>
  <section class="card">
    <h1>你好，Rust Web</h1>
    <p>这个页面由 <strong>Rust + Axum</strong> 提供服务。</p>
    <p>你已经可以在这个基础上继续加路由、模板和 API。</p>
    <span class="badge">运行地址: /</span>
  </section>
</body>
</html>"#,
    )
}
