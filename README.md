# 創業檢查 Skill

版本：1.0.0。語言：繁體中文。主要落地目標：Codex 本機 skill。

這個 skill 不重講創業課，而是回答：目前在哪個階段、證據支持什麼、最先解決哪一個問題、下一個最低必要的驗證是什麼。
目前交付為本機套件；尚未安裝到使用者環境，未執行真實模型的觸發或診斷效果評估。驗證記錄見 tests/VALIDATION.md。

## 設計

輸入專案現況與本輪決策後，依序執行：

鎖定決策 → 讀取證據 → 判斷階段 → 定向檢查 → 找一個主要卡點 → 最小驗證 → 比較結果。

四階段：賣得了／有人真用；賣得好／有理由選你；跑得穩／營運可持續；放得大／可交接擴展。
九模組：市場適配；人群場景痛點；需求與付費；定位品牌；功能信任與情緒；收入成本現金；交付品質；決策協作；創辦人目標與盲點。

不算總分，不預測成功率，不把缺資料判成沒市場。免費採用、付費需求與可持續營運分開。
這是從課程概念改寫的診斷工具，補充規則明列於 references/source-map.md；不是原課程完整還原。

## 檔案

```text
startup-checkup/
  SKILL.md
  README.md
  agents/openai.yaml
  references/framework.md
  references/evidence-and-experiments.md
  references/source-map.md
  templates/assessment.md
  templates/experiment.md
  scripts/validate.py
  tests/cases.json
  tests/test_validator.py
  tests/README.md
  tests/VALIDATION.md
```

只執行診斷不需 Python、API key、第三方服務或外部帳號。scripts/ 只提供維護者的靜態檢查，不由每次診斷自動執行。
SKILL.md 引用同資料夾的其他檔案，安裝時使用完整資料夾，不要只複製 SKILL.md。

## 安裝：先檢查既有環境，不自動覆寫

先確認要放在特定專案，還是個人共用。若使用者尚未指定，安裝者先詢問，不擅自挑一個專案或修改全域設定。
檢查既有 skill 目錄與同名項目；若已有 startup-checkup，先比對版本，未經同意不覆寫。

依建立時查核的 Codex 官方文件：

```text
專案範圍：<repo-root>/.agents/skills/startup-checkup/SKILL.md
個人範圍：~/.agents/skills/startup-checkup/SKILL.md
```

經授權後，把完整 startup-checkup 資料夾放入選定範圍。不要產生雙重巢狀的 startup-checkup/startup-checkup。
這次交付沒有替你做這個複製動作，也沒有改動 ~/.codex/config.toml。
其他平台未列為已測試的相容目標；不要依這份 README 推論所有 agent 都有相同路徑。

## 確認能被載入

在 Codex CLI／IDE 的 /skills 或 $ 選擇介面確認 startup-checkup 出現；新 skill 未出現時再重啟 Codex。
用下面的顯式呼叫開始。先跑 tests/cases.json 的五個案例，確認不只載入，行為也符合要求。
官方技術來源及查核日期見 references/source-map.md。

## 直接使用

```text
$startup-checkup
請根據本專案目前已提供的資料，做創業檢查。
這輪要決定：下一步應先驗證什麼。
只做只讀分析。先列已知與未知，再選一個主要卡點，設計一個最小驗證。
缺資料每輪最多問三題。不要修改網站、功能、價格或對外聯絡。
```

完整檢查：

```text
$startup-checkup
請做完整九模組檢查。沒有資料的地方標待驗證，不要湊分數。
檢查後只選一項主要卡點，不要產生九條平行開發計畫。
```

帶回結果：

```text
$startup-checkup
這是上次的假設、原判準與這次結果：［貼上資料］。
請先確認資料能否比較，再更新狀態。保留原判準，不要事後改成功定義。
```

本套件允許宿主依 description 自動觸發，但明確排除摘要、程式修正與單純 UI／文案任務。
顯式呼叫仍建議用於第一次測試，避免把「沒有觸發」和「診斷不好」混在一起。

## 驗證

於套件根目錄使用已安裝的 Python 3：

```bash
python3 scripts/validate.py .
python3 -m unittest discover -s tests -p 'test_validator.py' -v
```

第一項只檢查本套件的前置欄位、命名、相對連結、模板及五個測試案例結構，不是完整通用 YAML 驗證器或官方認證。
第二項測試檢查器能否攔截缺檔、壞連結或格式問題；不測模型的商業推理品質。
真實模型測試方式見 tests/README.md。未執行的項目必須保留未執行，不能因文件齊全就宣稱成功。

## 安全與停用

只讀是指令層約束，不是工具沙箱。由宿主限制可讀資料及工具權限；需要外聯、修改、付款或權限動作時另行取得授權。
只帶入必要、已去識別化的商業資料；本套件不含原始截圖、真實客戶資料、追蹤碼或網路上傳腳本。

安裝後可由宿主設定停用，或在使用者確認後移出本 skill 的資料夾；不得刪除整個 .agents/skills。
重裝或移除前，確認目的地與是否存在使用者自行修改的檔案。此套件未代執行安裝、重裝、移除或持續排程。
