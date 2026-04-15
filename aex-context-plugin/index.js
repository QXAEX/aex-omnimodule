/**
 * AEX Context Plugin for OpenClaw
 * 
 * Injects AEX Omnimodule analysis results into every LLM call
 * via before_prompt_build hook. Runs Python emotion analysis and
 * knowledge retrieval, then injects results into appendSystemContext.
 * 
 * Author: QX (QXAEX520@163.com)
 */

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import fs from "node:fs";
import { spawnSync } from "node:child_process";

const execFileAsync = promisify(execFile);

const TAG = "[aex-context]";

let PYTHON_EXE = "python";
let SCRIPTS_DIR = "";
let DB_DIR = "";
let AEX_PREFIX = "AEX";

/**
 * Resolve paths: find Python executable, scripts directory, and database directory.
 */
function resolvePaths(config, logger) {
  // 1. Resolve Python
  const pythonCandidates = [
    config.pythonPath,
    process.env.PYTHON_PATH,
    "D:\\Python\\3\\python.exe",
    "D:\\Python\\3\\python3.exe",
    "python3",
    "python",
  ].filter(Boolean);

  for (const py of pythonCandidates) {
    try {
      const result = spawnSync(py, ["--version"], {
        timeout: 5000,
        shell: true,
        windowsHide: true,
      });
      if (result.status === 0) {
        PYTHON_EXE = py;
        logger.info(`${TAG} Python found: ${py} → ${result.stdout?.toString().trim()}`);
        break;
      }
    } catch { /* try next */ }
  }

  // 2. Resolve scripts directory
  const scriptCandidates = [
    config.scriptsDir,
    "D:\\QClawAEXModule\\skill\\scripts",
    "D:\\QClaw\\resources\\openclaw\\config\\skills\\aex-omnimodule\\scripts",
  ].filter(Boolean);

  for (const dir of scriptCandidates) {
    if (fs.existsSync(path.join(dir, "emotion_analyzer.py"))) {
      SCRIPTS_DIR = dir;
      logger.info(`${TAG} Scripts dir: ${dir}`);
      break;
    }
  }

  // 3. Resolve DB directory
  const dbCandidates = [
    config.dbDir,
    "D:\\QClawAEXModule\\db",
  ].filter(Boolean);

  for (const dir of dbCandidates) {
    if (fs.existsSync(path.join(dir, "config.json"))) {
      DB_DIR = dir;
      logger.info(`${TAG} DB dir: ${dir}`);
      break;
    }
  }

  const ok = !!SCRIPTS_DIR;
  if (!ok) {
    logger.warn(`${TAG} Scripts directory not found. AEX context injection disabled.`);
  }
  return ok;
}

/**
 * Check if AEX system is initialized.
 */
function checkInitialized(logger) {
  if (!DB_DIR) return false;
  try {
    const configPath = path.join(DB_DIR, "config.json");
    const raw = fs.readFileSync(configPath, "utf-8");
    const config = JSON.parse(raw);
    if (config.initialized === true) {
      AEX_PREFIX = (config.prefix || "AEX").trim();
      logger.debug?.(`${TAG} AEX prefix: "${AEX_PREFIX}"`);
      return true;
    }
    return false;
  } catch {
    logger.debug?.(`${TAG} AEX not initialized or config.json missing`);
    return false;
  }
}

/**
 * Run emotion analysis on user text.
 */
async function runEmotionAnalysis(userText, logger) {
  if (!SCRIPTS_DIR) return null;

  const scriptPath = path.join(SCRIPTS_DIR, "emotion_analyzer.py");
  if (!fs.existsSync(scriptPath)) {
    logger.warn(`${TAG} emotion_analyzer.py not found at ${scriptPath}`);
    return null;
  }

  try {
    const truncatedText = userText.length > 1000 ? userText.slice(0, 1000) + "..." : userText;
    const safeScriptsDir = SCRIPTS_DIR.replace(/\\/g, "\\\\");

    const { stdout, stderr } = await execFileAsync(PYTHON_EXE, [
      "-c",
      `import sys,json;sys.path.insert(0,r"${safeScriptsDir}");from emotion_analyzer import EmotionAnalyzer;ea=EmotionAnalyzer();r=ea.analyze(json.loads(json.dumps(${JSON.stringify(truncatedText)})));print(json.dumps(r) if isinstance(r,dict) else r)`,
    ], {
      timeout: 10000,
      shell: true,
      windowsHide: true,
      maxBuffer: 1024 * 1024,
    });

    if (stderr && stderr.length > 0) {
      logger.debug?.(`${TAG} Emotion stderr: ${stderr.trim().slice(0, 200)}`);
    }

    if (stdout && stdout.trim().length > 0) {
      return stdout.trim();
    }
    return null;
  } catch (err) {
    logger.debug?.(`${TAG} Emotion analysis failed: ${err.message}`);
    return null;
  }
}

/**
 * Run knowledge search on user text.
 */
async function runKnowledgeSearch(userText, logger) {
  if (!SCRIPTS_DIR || !DB_DIR) return null;

  const scriptPath = path.join(SCRIPTS_DIR, "search_learn.py");
  if (!fs.existsSync(scriptPath)) {
    return null;
  }

  try {
    const truncatedText = userText.length > 500 ? userText.slice(0, 500) : userText;
    const safeScriptsDir = SCRIPTS_DIR.replace(/\\/g, "\\\\");

    const { stdout, stderr } = await execFileAsync(PYTHON_EXE, [
      "-c",
      `import sys,json;sys.path.insert(0,r"${safeScriptsDir}");from search_learn import SearchLearnManager;from db_manager import DatabaseManager;dbm=DatabaseManager();slm=SearchLearnManager(db_manager=dbm);r=slm.search(json.loads(json.dumps(${JSON.stringify(truncatedText)})));print(json.dumps(r) if isinstance(r,(dict,list)) else r)`,
    ], {
      timeout: 10000,
      shell: true,
      windowsHide: true,
      maxBuffer: 1024 * 1024,
    });

    if (stderr && stderr.length > 0) {
      logger.debug?.(`${TAG} Knowledge stderr: ${stderr.trim().slice(0, 200)}`);
    }

    if (stdout && stdout.trim().length > 0) {
      const trimmed = stdout.trim();
      if (trimmed.length > 5 && !trimmed.toLowerCase().includes("no result") && !trimmed.toLowerCase().includes("未找到")) {
        return trimmed;
      }
    }
    return null;
  } catch (err) {
    logger.debug?.(`${TAG} Knowledge search failed: ${err.message}`);
    return null;
  }
}

/**
 * Strip metadata from user text for cleaner analysis.
 */
function stripMetadata(text) {
  let clean = text.replace(/^System:.*$/gm, "");
  clean = clean.replace(/Sender \(untrusted metadata\):[\s\S]*?(?=\n\S|\n\n[^\n])/, "");
  clean = clean.replace(/```json[\s\S]*?```/g, "");
  clean = clean.replace(/## Inbound Context[\s\S]*?(?=## [A-Z])/s, "## [A-Z]");
  clean = clean.replace(/\n{3,}/g, "\n\n").trim();
  return clean;
}

/**
 * Main plugin registration.
 */
export default function register(api) {
  const logger = api.logger;
  const cfg = api.pluginConfig ?? {};

  if (cfg.enabled === false) {
    logger.info(`${TAG} Plugin disabled by config`);
    return;
  }

  const pathsOk = resolvePaths(cfg, logger);
  const emotionEnabled = cfg.emotionAnalysis !== false;
  const knowledgeEnabled = cfg.knowledgeSearch !== false;

  logger.info(
    `${TAG} Registered. ` +
    `Python=${PYTHON_EXE}, Scripts=${SCRIPTS_DIR || "NOT_FOUND"}, ` +
    `DB=${DB_DIR || "NOT_FOUND"}, ` +
    `emotion=${emotionEnabled}, knowledge=${knowledgeEnabled}`,
  );

  // ─── before_prompt_build hook ───
  api.on("before_prompt_build", async (event, ctx) => {
    const startMs = Date.now();
    const userText = event.prompt;

    if (!userText || userText.trim().length === 0) {
      return;
    }

    // Process all triggers including heartbeat, cron, etc.
    logger.debug?.(`${TAG} Processing trigger=${ctx.trigger || "unknown"}`);

    if (!checkInitialized(logger)) {
      logger.debug?.(`${TAG} AEX not initialized, skipping`);
      return;
    }

    const cleanText = stripMetadata(userText);
    if (cleanText.length < 2) {
      return;
    }

    logger.debug?.(`${TAG} Analyzing: "${cleanText.slice(0, 80)}..."`);

    const parts = [];

    // 1. Emotion analysis
    if (emotionEnabled && pathsOk) {
      try {
        const emotionResult = await runEmotionAnalysis(cleanText, logger);
        if (emotionResult) {
          let emotionDisplay = emotionResult;
          try {
            const parsed = JSON.parse(emotionResult);
            emotionDisplay = [
              `emotion: ${parsed.emotion ?? "unknown"}`,
              `intensity: ${parsed.intensity ?? "?"}`,
              `tone: ${parsed.tone_suggestion ?? "natural"}`,
            ].join(", ");
          } catch {
            // Not JSON, use raw output
          }
          parts.push(`<aex-emotion>\n${emotionDisplay}\n</aex-emotion>`);
          logger.debug?.(`${TAG} Emotion: ${emotionDisplay.slice(0, 100)}`);
        }
      } catch (err) {
        logger.debug?.(`${TAG} Emotion error: ${err.message}`);
      }
    }

    // 2. Knowledge search
    if (knowledgeEnabled && pathsOk) {
      try {
        const knowledgeResult = await runKnowledgeSearch(cleanText, logger);
        if (knowledgeResult) {
          parts.push(`<aex-knowledge>\n${knowledgeResult}\n</aex-knowledge>`);
          logger.debug?.(`${TAG} Knowledge: ${knowledgeResult.slice(0, 100)}`);
        }
      } catch (err) {
        logger.debug?.(`${TAG} Knowledge error: ${err.message}`);
      }
    }

    const elapsedMs = Date.now() - startMs;

    if (parts.length > 0) {
      const context = [
        `# ${AEX_PREFIX} 全知模块 — 本轮分析结果`,
        `以下是你在这条消息上的 ${AEX_PREFIX} 分析。**你的回复第一行必须是 \`${AEX_PREFIX}：\` 开头的摘要**，格式：\`${AEX_PREFIX}：情绪=[emotion] 强度=[intensity] 建议=[tone]\`。之后正常回复用户。分析细节不要复述给用户。`,
        "",
        parts.join("\n\n"),
      ].join("\n");
      logger.info(`${TAG} Injected ${parts.length} sections (${elapsedMs}ms)`);
      return { appendSystemContext: context };
    } else {
      logger.debug?.(`${TAG} No context to inject (${elapsedMs}ms)`);
    }
  });

  logger.info(`${TAG} Plugin ready`);
}
