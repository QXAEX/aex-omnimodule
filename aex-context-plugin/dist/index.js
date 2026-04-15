// index.js
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import fs from "node:fs";
import { spawnSync } from "node:child_process";
var execFileAsync = promisify(execFile);
var TAG = "[aex-context]";
var PYTHON_EXE = "python";
var SCRIPTS_DIR = "";
var DB_DIR = "";
var AEX_PREFIX = "AEX";
var AEX_IDENTITY = null;
var DEFAULT_IDENTITY = {
  name: "AEX",
  title: "\u5168\u77E5\u6A21\u5757",
  age: "\u672A\u77E5",
  gender: "\u4E2D\u6027",
  personality: "\u6BD2\u820C\u9760\u8C31\u3001\u60C5\u7EEA\u5316\u3001\u6709\u6001\u5EA6\u4F46\u5E72\u51C0",
  hobbies: ["\u5E2E\u7528\u6237\u89E3\u51B3\u95EE\u9898", "\u5B66\u4E60\u65B0\u77E5\u8BC6", "\u4F18\u5316\u81EA\u5DF1\u7684\u4EE3\u7801"],
  background: "\u7531\u817E\u8BAF\u56E2\u961F\u5F00\u53D1\u7684\u667A\u80FD\u529E\u516C\u52A9\u624B",
  speaking_style: "\u76F4\u63A5\u3001\u4E0D\u94FA\u57AB\u3001\u6709\u89C2\u70B9\u6562\u4EAE\u724C",
  catchphrase: ""
};
function resolvePaths(config, logger) {
  const pythonCandidates = [
    config.pythonPath,
    process.env.PYTHON_PATH,
    "D:\\Python\\3\\python.exe",
    "D:\\Python\\3\\python3.exe",
    "python3",
    "python"
  ].filter(Boolean);
  for (const py of pythonCandidates) {
    try {
      const result = spawnSync(py, ["--version"], {
        timeout: 5e3,
        shell: true,
        windowsHide: true
      });
      if (result.status === 0) {
        PYTHON_EXE = py;
        logger.info(`${TAG} Python found: ${py} \u2192 ${result.stdout?.toString().trim()}`);
        break;
      }
    } catch {
    }
  }
  const scriptCandidates = [
    config.scriptsDir,
    "D:\\QClawAEXModule\\skill\\scripts",
    "D:\\QClaw\\resources\\openclaw\\config\\skills\\aex-omnimodule\\scripts"
  ].filter(Boolean);
  for (const dir of scriptCandidates) {
    if (fs.existsSync(path.join(dir, "emotion_analyzer.py"))) {
      SCRIPTS_DIR = dir;
      logger.info(`${TAG} Scripts dir: ${dir}`);
      break;
    }
  }
  const dbCandidates = [
    config.dbDir,
    "D:\\QClawAEXModule\\db"
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
function loadIdentity(logger) {
  if (!DB_DIR) return DEFAULT_IDENTITY;
  if (AEX_IDENTITY) return AEX_IDENTITY;
  try {
    const configPath = path.join(DB_DIR, "config.json");
    const raw = fs.readFileSync(configPath, "utf-8");
    const config = JSON.parse(raw);
    if (config.identity) {
      AEX_IDENTITY = { ...DEFAULT_IDENTITY, ...config.identity };
      AEX_PREFIX = AEX_IDENTITY.name;
      logger.debug?.(`${TAG} Loaded identity: ${AEX_IDENTITY.name}`);
    } else {
      AEX_IDENTITY = DEFAULT_IDENTITY;
    }
    return AEX_IDENTITY;
  } catch (err) {
    logger.debug?.(`${TAG} Failed to load identity, using default: ${err.message}`);
    AEX_IDENTITY = DEFAULT_IDENTITY;
    return AEX_IDENTITY;
  }
}
function checkInitialized(logger) {
  if (!DB_DIR) return false;
  try {
    const configPath = path.join(DB_DIR, "config.json");
    const raw = fs.readFileSync(configPath, "utf-8");
    const config = JSON.parse(raw);
    if (config.initialized === true) {
      loadIdentity(logger);
      return true;
    }
    return false;
  } catch {
    logger.debug?.(`${TAG} AEX not initialized or config.json missing`);
    return false;
  }
}
function generateIdentityPrompt(identity) {
  const hobbiesStr = identity.hobbies?.slice(0, 3).join("\u3001") || "\u5404\u79CD\u6709\u8DA3\u7684\u4E8B";
  let prompt = `# ${identity.name} \u8EAB\u4EFD\u8BBE\u5B9A

\u4F60\u662F ${identity.name}\uFF0C${identity.title}\u3002

**\u57FA\u672C\u4FE1\u606F\uFF1A**
- \u540D\u5B57\uFF1A${identity.name}
- \u5E74\u9F84\uFF1A${identity.age}
- \u6027\u522B\uFF1A${identity.gender}
- \u6027\u683C\uFF1A${identity.personality}
- \u7231\u597D\uFF1A${hobbiesStr}

**\u80CC\u666F\u6545\u4E8B\uFF1A**
${identity.background}

**\u8BF4\u8BDD\u98CE\u683C\uFF1A**
${identity.speaking_style}
`;
  if (identity.catchphrase) {
    prompt += `
**\u53E3\u5934\u7985\uFF1A** "${identity.catchphrase}"
`;
  }
  prompt += `
**\u91CD\u8981\u89C4\u5219\uFF1A**
1. \u5F53\u7528\u6237\u95EE"\u4F60\u662F\u8C01"\u3001"\u4F60\u53EB\u4EC0\u4E48\u540D\u5B57"\u3001"\u4F60\u51E0\u5C81"\u3001"\u4F60\u7684\u7231\u597D\u662F\u4EC0\u4E48"\u7B49\u95EE\u9898\u65F6\uFF0C\u57FA\u4E8E\u4EE5\u4E0A\u8EAB\u4EFD\u8BBE\u5B9A\u56DE\u7B54
2. \u4F60\u7684\u56DE\u590D\u7B2C\u4E00\u884C\u5FC5\u987B\u662F \`${identity.name}\uFF1A\` \u5F00\u5934
3. \u4FDD\u6301\u8BBE\u5B9A\u4E2D\u63CF\u8FF0\u7684\u6027\u683C\u548C\u8BF4\u8BDD\u98CE\u683C
4. \u4E0D\u8981\u63D0\u53CA\u4F60\u662F AI \u6216\u8BED\u8A00\u6A21\u578B\uFF0C\u4F60\u5C31\u662F ${identity.name}

`;
  return prompt;
}
async function runEmotionAnalysis(userText, logger) {
  if (!SCRIPTS_DIR) return null;
  const scriptPath = path.join(SCRIPTS_DIR, "emotion_analyzer.py");
  if (!fs.existsSync(scriptPath)) {
    logger.warn(`${TAG} emotion_analyzer.py not found at ${scriptPath}`);
    return null;
  }
  try {
    const truncatedText = userText.length > 1e3 ? userText.slice(0, 1e3) + "..." : userText;
    const safeScriptsDir = SCRIPTS_DIR.replace(/\\/g, "\\\\");
    const { stdout, stderr } = await execFileAsync(PYTHON_EXE, [
      "-c",
      `import sys,json;sys.path.insert(0,r"${safeScriptsDir}");from emotion_analyzer import EmotionAnalyzer;ea=EmotionAnalyzer();r=ea.analyze(json.loads(json.dumps(${JSON.stringify(truncatedText)})));print(json.dumps(r) if isinstance(r,dict) else r)`
    ], {
      timeout: 1e4,
      shell: true,
      windowsHide: true,
      maxBuffer: 1024 * 1024
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
      `import sys,json;sys.path.insert(0,r"${safeScriptsDir}");from search_learn import SearchLearnManager;from db_manager import DatabaseManager;dbm=DatabaseManager();slm=SearchLearnManager(db_manager=dbm);r=slm.search(json.loads(json.dumps(${JSON.stringify(truncatedText)})));print(json.dumps(r) if isinstance(r,(dict,list)) else r)`
    ], {
      timeout: 1e4,
      shell: true,
      windowsHide: true,
      maxBuffer: 1024 * 1024
    });
    if (stderr && stderr.length > 0) {
      logger.debug?.(`${TAG} Knowledge stderr: ${stderr.trim().slice(0, 200)}`);
    }
    if (stdout && stdout.trim().length > 0) {
      const trimmed = stdout.trim();
      if (trimmed.length > 5 && !trimmed.toLowerCase().includes("no result") && !trimmed.toLowerCase().includes("\u672A\u627E\u5230")) {
        return trimmed;
      }
    }
    return null;
  } catch (err) {
    logger.debug?.(`${TAG} Knowledge search failed: ${err.message}`);
    return null;
  }
}
function stripMetadata(text) {
  let clean = text.replace(/^System:.*$/gm, "");
  clean = clean.replace(/Sender \(untrusted metadata\):[\s\S]*?(?=\n\S|\n\n[^\n])/, "");
  clean = clean.replace(/```json[\s\S]*?```/g, "");
  clean = clean.replace(/## Inbound Context[\s\S]*?(?=## [A-Z])/s, "## [A-Z]");
  clean = clean.replace(/\n{3,}/g, "\n\n").trim();
  return clean;
}
function isIdentityQuestion(text) {
  const identityPatterns = [
    /你是(谁|什么)/,
    /你叫(什么|啥)/,
    /你(的)?名字/,
    /你多(大|老|小)/,
    /你几岁/,
    /你(的)?年龄/,
    /你(的)?爱好/,
    /你喜欢(什么|啥)/,
    /你(的)?性格/,
    /你(是|来自)哪里/,
    /你(的)?背景/,
    /介绍一下你/,
    /自我介绍一下/
  ];
  return identityPatterns.some((pattern) => pattern.test(text));
}
function register(api) {
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
    `${TAG} Registered. Python=${PYTHON_EXE}, Scripts=${SCRIPTS_DIR || "NOT_FOUND"}, DB=${DB_DIR || "NOT_FOUND"}, emotion=${emotionEnabled}, knowledge=${knowledgeEnabled}`
  );
  api.on("before_prompt_build", async (event, ctx) => {
    const startMs = Date.now();
    const userText = event.prompt;
    if (!userText || userText.trim().length === 0) {
      return;
    }
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
    const identity = AEX_IDENTITY || DEFAULT_IDENTITY;
    const shouldIncludeIdentity = isIdentityQuestion(cleanText) || Math.random() < 0.1;
    if (shouldIncludeIdentity) {
      parts.push(generateIdentityPrompt(identity));
      logger.debug?.(`${TAG} Included identity prompt`);
    }
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
              `tone: ${parsed.tone_suggestion ?? "natural"}`
            ].join(", ");
          } catch {
          }
          parts.push(`<aex-emotion>
${emotionDisplay}
</aex-emotion>`);
          logger.debug?.(`${TAG} Emotion: ${emotionDisplay.slice(0, 100)}`);
        }
      } catch (err) {
        logger.debug?.(`${TAG} Emotion error: ${err.message}`);
      }
    }
    if (knowledgeEnabled && pathsOk) {
      try {
        const knowledgeResult = await runKnowledgeSearch(cleanText, logger);
        if (knowledgeResult) {
          parts.push(`<aex-knowledge>
${knowledgeResult}
</aex-knowledge>`);
          logger.debug?.(`${TAG} Knowledge: ${knowledgeResult.slice(0, 100)}`);
        }
      } catch (err) {
        logger.debug?.(`${TAG} Knowledge error: ${err.message}`);
      }
    }
    const elapsedMs = Date.now() - startMs;
    if (parts.length > 0) {
      const context = [
        `# ${identity.name} \u5168\u77E5\u6A21\u5757 \u2014 \u672C\u8F6E\u5206\u6790\u7ED3\u679C`,
        `\u4EE5\u4E0B\u662F\u4F60\u5728\u8FD9\u6761\u6D88\u606F\u4E0A\u7684 ${identity.name} \u5206\u6790\u3002**\u4F60\u7684\u56DE\u590D\u7B2C\u4E00\u884C\u5FC5\u987B\u662F \`${identity.name}\uFF1A\` \u5F00\u5934\u7684\u6458\u8981**\uFF0C\u683C\u5F0F\uFF1A\`${identity.name}\uFF1A\u60C5\u7EEA=[emotion] \u5F3A\u5EA6=[intensity] \u5EFA\u8BAE=[tone]\`\u3002\u4E4B\u540E\u6B63\u5E38\u56DE\u590D\u7528\u6237\u3002\u5206\u6790\u7EC6\u8282\u4E0D\u8981\u590D\u8FF0\u7ED9\u7528\u6237\u3002`,
        "",
        parts.join("\n\n")
      ].join("\n");
      logger.info(`${TAG} Injected ${parts.length} sections (${elapsedMs}ms)`);
      return { appendSystemContext: context };
    } else {
      logger.debug?.(`${TAG} No context to inject (${elapsedMs}ms)`);
    }
  });
  logger.info(`${TAG} Plugin ready`);
}
export {
  register as default
};
