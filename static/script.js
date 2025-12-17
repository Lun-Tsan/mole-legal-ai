// 定義處理步驟 (用來顯示動畫)
const STEPS = [
    "🔍 Classifier Agent: 正在分析案件領域...",
    "📚 Expert Agent: 正在檢索法律資料庫...",
    "⚖️ Retrieval Agent: 正在比對相關判例...",
    "✍️ Synthesizer Agent: 正在撰寫法律分析報告..."
];

async function submitQuery() {
    const query = document.getElementById('queryInput').value;
    if (!query) return alert("請輸入案件內容！");

    // 1. 初始化 UI 狀態
    const btn = document.getElementById('submitBtn');
    const processDiv = document.getElementById('process-indicator');
    const resultArea = document.getElementById('result-area');
    
    btn.disabled = true;
    btn.innerText = "⏳ 專家小隊工作中...";
    resultArea.style.display = 'none';
    processDiv.style.display = 'block';
    processDiv.innerHTML = ''; // 清空舊進度

    // 2. 啟動「模擬」進度動畫 (增加使用者耐心)
    let stepIndex = 0;
    const intervalId = setInterval(() => {
        if (stepIndex < STEPS.length) {
            const p = document.createElement('div');
            p.className = 'step active';
            p.innerHTML = `<span class="step-icon">▶</span> ${STEPS[stepIndex]}`;
            processDiv.appendChild(p);
            
            // 讓舊的步驟變淡
            if(processDiv.children.length > 1){
                processDiv.children[processDiv.children.length-2].classList.remove('active');
                processDiv.children[processDiv.children.length-2].innerHTML = `✓ ${STEPS[stepIndex-1]}`;
            }
            stepIndex++;
        }
    }, 1200); // 每 1.2 秒顯示下一個步驟

    try {
        // 3. 呼叫後端 API (這會花幾秒鐘)
        const response = await fetch('/api/consult', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();

        // 停止動畫
        clearInterval(intervalId);
        processDiv.innerHTML = '<div class="step active" style="color:green">✅ 分析完成！</div>';

        // 4. 渲染結果
        renderResults(data);

    } catch (error) {
        clearInterval(intervalId);
        processDiv.innerHTML = '<div class="step" style="color:red">❌ 系統發生錯誤，請稍後再試。</div>';
        console.error(error);
    } finally {
        btn.disabled = false;
        btn.innerText = "開始分析案件";
    }
}

function renderResults(data) {
    // A. 顯示總結
    // 將換行符號轉為 <br>
    const cleanSummary = data.summary.replace(/\n/g, '<br>');
    document.getElementById('res-summary').innerHTML = cleanSummary;

    // B. 顯示法條
    const statuteHtml = data.statutes.map(s => {
        // 判斷是用民法還是刑法標籤
        const badgeClass = s.law_name.includes("刑") ? "badge-criminal" : "badge-civil";
        return `
        <div class="card">
            <h3>
                <span class="badge ${badgeClass}">${s.law_name}</span>
                ${s.article_id}
            </h3>
            <p>${s.content}</p>
        </div>`;
    }).join('');
    document.getElementById('res-statutes').innerHTML = statuteHtml || "<p>無相關法條。</p>";

    // C. 顯示判例
    const caseHtml = data.cases.map(c => `
        <div class="card" style="border-left: 4px solid #8e44ad;">
            <h3>
                <span class="badge badge-court">${c.court}</span>
                ${c.case_id}
            </h3>
            <p>${c.summary}</p>
        </div>
    `).join('');
    document.getElementById('res-cases').innerHTML = caseHtml || "<p>無相關判例。</p>";

    // 顯示區域
    document.getElementById('result-area').style.display = 'block';
    
    // 平滑捲動到結果區
    document.getElementById('result-area').scrollIntoView({ behavior: 'smooth' });
}
// --- 側邊欄與歷史紀錄邏輯 ---

// 頁面載入時，抓取歷史紀錄
document.addEventListener("DOMContentLoaded", loadHistory);

function toggleSidebar() {
    const sidebar = document.getElementById('history-sidebar');
    sidebar.classList.toggle('open');
}

async function loadHistory() {
    try {
        const res = await fetch('/api/history');
        const records = await res.json();
        
        const listDiv = document.getElementById('history-list');
        listDiv.innerHTML = ''; 

        if (records.length === 0) {
            listDiv.innerHTML = '<p style="color:#aaa; text-align:center; margin-top:20px;">尚無紀錄</p>';
            return;
        }

        records.forEach(rec => {
            const item = document.createElement('div');
            item.className = 'history-item';
            
            // 時間格式化
            const dateStr = new Date(rec.created_at).toLocaleString('zh-TW', { 
                month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' 
            });
            
            // 修改 HTML 結構：加入刪除按鈕
            // 注意 onclick="deleteHistoryItem(..., event)"
            item.innerHTML = `
                <div class="history-content">
                    <div class="history-date">${dateStr}</div>
                    <div class="history-query">${rec.query}</div>
                </div>
                <button class="delete-btn" onclick="deleteHistoryItem(${rec.id}, event)">✕</button>
            `;
            
            // 點擊整個卡片 -> 還原
            item.onclick = () => restoreHistory(rec);
            
            listDiv.appendChild(item);
        });
    } catch (err) {
        console.error("無法載入歷史紀錄", err);
    }
}

// 新增：刪除功能
async function deleteHistoryItem(id, event) {
    // 1. 重要：阻止事件冒泡 (避免觸發還原)
    event.stopPropagation();
    
    if (!confirm("確定要刪除這筆紀錄嗎？")) return;

    try {
        // 2. 呼叫後端 API
        await fetch(`/api/history/${id}`, { method: 'DELETE' });
        
        // 3. 重新載入列表
        loadHistory();
        
    } catch (err) {
        alert("刪除失敗");
        console.error(err);
    }
}

function restoreHistory(record) {
    // 1. 填回輸入框
    document.getElementById('queryInput').value = record.query;
    
    // 2. 顯示結果 (使用之前寫好的 renderResults 函式)
    renderResults(record.result);
    
    // 3. 關閉側邊欄
    toggleSidebar();
    
    // 4. 自動捲動到結果
    document.getElementById('result-area').scrollIntoView({ behavior: 'smooth' });
}

function fillPrompt(type) {
    const prompts = {
        '車禍': '我昨天開車綠燈直行，結果被一台闖紅燈的機車撞到側面，對方骨折但我沒事。現在對方說我是開車的「應注意而未注意」，要求我賠償醫藥費跟精神損失，請問我真的要賠嗎？',
        '租屋': '我租約還沒到期，但房東說要把房子賣掉，叫我下個月底前搬走，還說如果不搬就要扣我押金，請問這樣合法嗎？我可以要求違約金嗎？',
        '罵人': '我在網路上跟人吵架，對方在公開留言區罵我「腦殘」、「生兒子沒屁眼」，我覺得受辱，請問可以告他什麼？',
        '勞資': '我是飲料店員工，老闆規定如果做錯飲料要扣薪水 500 元，結果我上個月薪水被扣了 2000 元，低於基本工資，請問老闆這樣違反勞基法嗎？'
    };
    
    const input = document.getElementById('queryInput');
    input.value = prompts[type];
    
    // 視覺回饋：讓輸入框閃一下
    input.focus();
    input.style.borderColor = '#3498db';
    setTimeout(() => input.style.borderColor = '#eee', 300);
}

// 修改原本的 submitQuery，讓它成功後順便重新整理歷史列表
const originalSubmit = submitQuery;
submitQuery = async function() {
    await originalSubmit(); // 執行原本的提交
    // 提交完成後，重新抓取最新的歷史紀錄
    loadHistory();
}