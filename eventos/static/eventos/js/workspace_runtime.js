(() => {
  "use strict";

  const SHELL = "[data-workspace-shell]";
  let controller = null;

  function getShell() {
    return document.querySelector(SHELL);
  }

  function sameOrigin(url) {
    return url.origin === window.location.origin;
  }

  function isModifiedClick(event) {
    return event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
  }

  function rememberScroll(url = window.location.href) {
    try {
      sessionStorage.setItem(
        `dirtec:workspace:scroll:${url}`,
        JSON.stringify({
          x: window.scrollX,
          y: window.scrollY,
          tabs: document.querySelector("[data-workspace-tabs]")?.scrollLeft || 0,
        })
      );
    } catch (_) {}
  }

  function storedScroll(url = window.location.href) {
    try {
      return JSON.parse(sessionStorage.getItem(`dirtec:workspace:scroll:${url}`) || "null");
    } catch (_) {
      return null;
    }
  }

  function setLoading(active) {
    document.documentElement.classList.toggle("workspace-is-loading", active);
    getShell()?.setAttribute("aria-busy", active ? "true" : "false");
  }

  function shouldHandleLink(link, event) {
    if (!link || !getShell() || isModifiedClick(event)) return false;
    if (!link.closest(SHELL)) return false;
    if (link.hasAttribute("data-workspace-native") || link.hasAttribute("download")) return false;
    if (link.target && link.target !== "_self") return false;

    const raw = link.getAttribute("href");
    if (!raw || raw.startsWith("#") || raw.startsWith("javascript:")) return false;

    const url = new URL(link.href, window.location.href);
    return sameOrigin(url);
  }

  function shouldHandleForm(form) {
    if (!form || !getShell() || !form.closest(SHELL)) return false;
    if (form.hasAttribute("data-workspace-native")) return false;
    if (form.target && form.target !== "_self") return false;

    const action = new URL(form.getAttribute("action") || window.location.href, window.location.href);
    return sameOrigin(action);
  }

  function syncStyles(nextDocument) {
    const existing = new Set(
      [...document.querySelectorAll('link[rel="stylesheet"][href]')].map((x) => new URL(x.href, location.href).href)
    );

    nextDocument.querySelectorAll('link[rel="stylesheet"][href]').forEach((node) => {
      const href = new URL(node.href, location.href).href;
      if (existing.has(href)) return;
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      document.head.appendChild(link);
      existing.add(href);
    });
  }

  async function syncScripts(nextDocument) {
    const existing = new Set(
      [...document.querySelectorAll("script[src]")].map((x) => new URL(x.src, location.href).href)
    );

    for (const node of nextDocument.querySelectorAll("script[src]")) {
      const src = new URL(node.src, location.href).href;
      if (existing.has(src)) continue;

      await new Promise((resolve) => {
        const script = document.createElement("script");
        script.src = src;
        script.type = node.type || "text/javascript";
        script.onload = resolve;
        script.onerror = resolve;
        document.body.appendChild(script);
      });

      existing.add(src);
    }
  }

  function restorePosition({ oldUrl, newUrl, previous, moduleNavigation, popstate }) {
    const tabs = document.querySelector("[data-workspace-tabs]");

    if (popstate) {
      const stored = storedScroll(newUrl);
      if (stored) {
        window.scrollTo(stored.x || 0, stored.y || 0);
        if (tabs) tabs.scrollLeft = stored.tabs || 0;
        return;
      }
    }

    if (tabs && previous) tabs.scrollLeft = previous.tabs || 0;

    const oldParsed = new URL(oldUrl, location.href);
    const newParsed = new URL(newUrl, location.href);

    if (oldParsed.pathname === newParsed.pathname && previous) {
      // Editar, guardar, filtrar o responder dentro del mismo módulo:
      // conserva exactamente el punto donde estaba trabajando el usuario.
      window.scrollTo(previous.x || 0, previous.y || 0);
      return;
    }

    if (moduleNavigation) {
      const content = document.querySelector("[data-workspace-content]");
      if (content) {
        const top = content.getBoundingClientRect().top + window.scrollY - 16;
        window.scrollTo({ top: Math.max(top, 0), behavior: "instant" });
        return;
      }
    }

    window.scrollTo(0, 0);
  }

  async function navigate(url, {
    method = "GET",
    body = null,
    replace = false,
    popstate = false,
    moduleNavigation = false,
  } = {}) {
    if (!getShell()) {
      window.location.assign(url);
      return;
    }

    rememberScroll();

    const oldUrl = window.location.href;
    const previous = {
      x: window.scrollX,
      y: window.scrollY,
      tabs: document.querySelector("[data-workspace-tabs]")?.scrollLeft || 0,
    };

    controller?.abort();
    controller = new AbortController();
    setLoading(true);

    try {
      const response = await fetch(url, {
        method,
        body,
        credentials: "same-origin",
        redirect: "follow",
        headers: {
          "X-DIRTEC-Workspace": "1",
          "X-Requested-With": "XMLHttpRequest",
        },
        signal: controller.signal,
      });

      const type = response.headers.get("content-type") || "";

      // Excel, PDF u otras descargas conservan navegación nativa.
      if (!type.includes("text/html")) {
        if (method === "GET") window.location.assign(url);
        else window.location.reload();
        return;
      }

      const html = await response.text();
      const nextDocument = new DOMParser().parseFromString(html, "text/html");
      const nextShell = nextDocument.querySelector(SHELL);

      if (!nextShell) {
        window.location.assign(response.url || url);
        return;
      }

      syncStyles(nextDocument);
      if (nextDocument.title) document.title = nextDocument.title;

      getShell().replaceWith(nextShell);

      const finalUrl = response.url || url;
      if (!popstate) {
        if (replace) history.replaceState({ dirtecWorkspace: true }, "", finalUrl);
        else history.pushState({ dirtecWorkspace: true }, "", finalUrl);
      }

      await syncScripts(nextDocument);

      restorePosition({
        oldUrl,
        newUrl: finalUrl,
        previous,
        moduleNavigation,
        popstate,
      });

      document.dispatchEvent(new CustomEvent("dirtec:workspace:loaded", {
        detail: { url: finalUrl, moduleNavigation },
      }));
    } catch (error) {
      if (error?.name === "AbortError") return;
      console.error("DIRTEC Workspace navigation failed:", error);
      window.location.assign(url);
    } finally {
      setLoading(false);
    }
  }

  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (!shouldHandleLink(link, event)) return;

    event.preventDefault();
    navigate(link.href, {
      moduleNavigation: link.hasAttribute("data-workspace-module-link"),
    });
  });

  document.addEventListener("submit", (event) => {
    const form = event.target.closest("form");
    if (!shouldHandleForm(form)) return;

    event.preventDefault();

    const method = (form.method || "GET").toUpperCase();
    const action = new URL(form.getAttribute("action") || location.href, location.href);
    const data = new FormData(form);

    if (method === "GET") {
      const params = new URLSearchParams();
      for (const [key, value] of data.entries()) {
        if (typeof value === "string") params.append(key, value);
      }
      action.search = params.toString();
      navigate(action.href);
      return;
    }

    navigate(action.href, { method, body: data });
  });

  window.addEventListener("popstate", () => {
    navigate(location.href, { replace: true, popstate: true });
  });

  window.addEventListener("beforeunload", () => rememberScroll());

  if ("scrollRestoration" in history) {
    history.scrollRestoration = "manual";
  }

  history.replaceState(
    { ...(history.state || {}), dirtecWorkspace: true },
    "",
    location.href
  );

  window.DIRTECWorkspace = Object.freeze({ navigate, rememberScroll });
})();