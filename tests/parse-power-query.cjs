// Syntax only: install @microsoft/powerquery-parser externally or pass its path.
const fs = require("node:fs");
const path = require("node:path");
const pq = require(process.argv[2] || "@microsoft/powerquery-parser");
const root = path.resolve(__dirname, "..");

(async () => {
    for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
        if (!entry.isFile()) continue;
        const source = fs.readFileSync(path.join(root, entry.name), "utf8");
        if (!source.startsWith("let\n")) continue;
        const result = await pq.TaskUtils.tryLexParse(pq.DefaultSettings, source);
        console.log(`${entry.name}: ${result.stage} / ${result.resultKind}`);
        if (result.resultKind !== "Ok") {
            console.error(result.error);
            process.exitCode = 1;
        }
    }
})().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
