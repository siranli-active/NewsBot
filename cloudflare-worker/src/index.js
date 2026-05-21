export default {
  async scheduled(event, env, ctx) {
    const response = await fetch(
      "https://api.github.com/repos/siranli-active/NewsBot/actions/workflows/daily_brief.yml/dispatches",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "newsbot-cloudflare-scheduler",
        },
        body: JSON.stringify({
          ref: "main",
          inputs: {
            source: "cloudflare",
          },
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`GitHub dispatch failed: ${response.status} ${await response.text()}`);
    }
  },
};
