// ==UserScript==
// @name         Jira功能拓展优化整合版
// @namespace    http://tampermonkey.net/
// @version      2.2
// @description  关键词高亮、当前用户加粗、复制按钮、bug提示按钮、时间显示优化等功能的整合
// @author       jiale.pan
// @match        http://jira-ex.transsion.com/*
// @grant        none
// @updateURL    https://raw.githubusercontent.com/Lemou-Memo/mmi_work/refs/heads/master/%E8%84%9A%E6%9C%AC/Jira%20chrome.js
// @downloadURL  https://raw.githubusercontent.com/Lemou-Memo/mmi_work/refs/heads/master/%E8%84%9A%E6%9C%AC/Jira%20chrome.js
// ==/UserScript==

(function() {
    'use strict';

    // ==关键词高亮和当前用户加粗部分==
    let keywords = JSON.parse(localStorage.getItem('highlightedKeywords')) || ["标准化", "三方", "粉丝"];
    const effectStyle = `
        .highlighted-keyword {
            color: #000;
            font-weight: bold;
            text-decoration: underline;
        }
        .current-user {
            color: #008000;
            font-weight: bold;
        }
        .floating-panel {
            display: none;
            position: fixed;
            bottom: 80px;
            left: 20px;
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 10px;
            width: 250px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
            z-index: 10000;
        }
        .floating-panel input {
            width: calc(100% - 60px);
            padding: 5px;
            margin-bottom: 10px;
            border-radius: 4px;
            border: 1px solid #ccc;
        }
        .floating-panel button {
            width: 40px;
            padding: 5px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .keyword-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            align-items: center;
        }
        .keyword-item span {
            flex-grow: 1;
        }
        .keyword-item .delete-btn {
            margin-left: 10px;
            background-color: #dc3545;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            padding: 2px 5px;
        }
        .toggle-button {
            position: fixed;
            bottom: 20px;
            left: 20px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            font-size: 24px;
            cursor: pointer;
            z-index: 10000;
        }
    `;
    const styleSheet = document.createElement("style");
    styleSheet.type = "text/css";
    styleSheet.innerText = effectStyle;
    document.head.appendChild(styleSheet);

    function highlightText(node) {
        if (node.nodeType === 3) {
            let text = node.nodeValue;
            let parent = node.parentNode;
            let modifiedText = text;

            for (let keyword of keywords) {
                let regex = new RegExp(`(${keyword})`, "gi");
                if (regex.test(modifiedText)) {
                    modifiedText = modifiedText.replace(regex, `<span class="highlighted-keyword" data-keyword="${keyword}">$1</span>`);
                }
            }

            if (modifiedText !== text) {
                let span = document.createElement('span');
                span.innerHTML = modifiedText;
                parent.replaceChild(span, node);
            }
        } else if (node.nodeType === 1 && node.childNodes) {
            for (let i = 0; i < node.childNodes.length; i++) {
                highlightText(node.childNodes[i]);
            }
        }
    }

    function clearHighlights() {
        document.querySelectorAll('.highlighted-keyword').forEach(element => {
            const textNode = document.createTextNode(element.innerText);
            element.parentNode.replaceChild(textNode, element);
        });
    }

    function getCurrentUser() {
        const userElement = document.querySelector('#header-details-user-fullname');
        return userElement ? userElement.getAttribute('data-username') : null;
    }

    function highlightCurrentUser() {
        const currentUsername = getCurrentUser();
        if (currentUsername) {
            document.querySelectorAll('td.assignee a.user-hover, td.reporter a.user-hover').forEach(userLink => {
                const username = userLink.getAttribute('rel');
                if (username === currentUsername) {
                    userLink.classList.add('current-user');
                }
            });
        }
    }
    highlightCurrentUser();
    // function updateHighlights() {
    //     clearHighlights();
    //     highlightText(document.body);
    // }
    // updateHighlights();

    // const floatingPanel = document.createElement("div");
    // floatingPanel.className = "floating-panel";
    // floatingPanel.innerHTML = `
    //     <input type="text" id="newKeyword" placeholder="添加关键词" />
    //     <button id="addKeyword">+</button>
    //     <div id="keywordList"></div>
    // `;
    // document.body.appendChild(floatingPanel);

    // const toggleButton = document.createElement("button");
    // toggleButton.className = "toggle-button";
    // toggleButton.textContent = "☰";
    // document.body.appendChild(toggleButton);

    // toggleButton.addEventListener("click", function() {
    //     floatingPanel.style.display = floatingPanel.style.display === "none" || !floatingPanel.style.display ? "block" : "none";
    //     renderKeywordList();
    // });

    // function renderKeywordList() {
    //     const keywordListDiv = document.getElementById("keywordList");
    //     keywordListDiv.innerHTML = "";

    //     keywords.forEach((keyword, index) => {
    //         const keywordItem = document.createElement("div");
    //         keywordItem.className = "keyword-item";
    //         keywordItem.innerHTML = `
    //             <span>${keyword}</span>
    //             <button class="delete-btn" data-index="${index}">删除</button>
    //         `;
    //         keywordListDiv.appendChild(keywordItem);
    //     });

    //     document.querySelectorAll(".delete-btn").forEach(button => {
    //         button.addEventListener("click", function() {
    //             const index = this.getAttribute("data-index");
    //             keywords.splice(index, 1);
    //             saveKeywords();
    //             updateHighlights();
    //             renderKeywordList();
    //         });
    //     });
    // }

    // function saveKeywords() {
    //     localStorage.setItem('highlightedKeywords', JSON.stringify(keywords));
    // }

    // function checkKeywordContainment(newKeyword) {
    //     for (let keyword of keywords) {
    //         if (keyword.includes(newKeyword) || newKeyword.includes(keyword)) {
    //             return true;
    //         }
    //     }
    //     return false;
    // }

    // document.getElementById("addKeyword").addEventListener("click", function() {
    //     const newKeyword = document.getElementById("newKeyword").value.trim();
    //     if (newKeyword && !keywords.includes(newKeyword)) {
    //         if (!checkKeywordContainment(newKeyword)) {
    //             keywords.push(newKeyword);
    //             saveKeywords();
    //             document.getElementById("newKeyword").value = "";
    //             updateHighlights();
    //             renderKeywordList();
    //         } else {
    //             alert("关键词与现有关键词存在包含关系，无法添加！");
    //         }
    //     } else if (keywords.includes(newKeyword)) {
    //         alert("关键词已存在！");
    //     }
    // });
    // renderKeywordList();

    // ==Jira功能拓展部分==
    function createCopyButton(anchor, row) {
        const button = document.createElement('button');
        button.textContent = '复制链接';
        Object.assign(button.style, {
            marginLeft: '5px',
            fontSize: '12px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '2px 5px',
            cursor: 'pointer'
        });

        button.addEventListener('click', () => copyToClipboard(anchor.href));
        button.addEventListener('dblclick', () => copySummaryContent(row));

        return button;
    }

    function copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text)
                .then(() => showNotification('链接已复制到剪贴板!', '#28a745'))
                .catch(err => showNotification('复制链接失败: ' + err, '#dc3545'));
        } else {
            fallbackCopyToClipboard(text);
        }
    }

    function fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showNotification('链接已复制到剪贴板!', '#28a745');
        } catch (err) {
            showNotification('复制链接失败: ' + err, '#dc3545');
        }
        document.body.removeChild(textArea);
    }

    function showNotification(message, backgroundColor) {
        const notification = document.createElement('div');
        notification.textContent = message;
        Object.assign(notification.style, {
            position: 'fixed',
            bottom: '10px',
            right: '10px',
            backgroundColor: backgroundColor,
            color: 'white',
            padding: '10px',
            borderRadius: '5px',
            zIndex: '10000'
        });
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 2000);
    }

    function updateColumnHeaders() {
        const headers = document.querySelectorAll('th.colHeaderLink span');
        headers.forEach(span => {
            switch (span.textContent) {
                case '关键字':
                    span.textContent = '关键字(点击本页面跳转)';
                    break;
                case '概要':
                    span.textContent = '概要(点击新建页面跳转)';
                    break;
            }
        });
    }

    function createMarkButton(row) {
        const button = document.createElement('button');
        Object.assign(button.style, {
            fontSize: '12px',
            backgroundColor: '#343a40',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            padding: '2px 5px',
            cursor: 'pointer',
            marginLeft: '5px'
        });

        updateButton(row, button);

        button.addEventListener('click', (event) => {
            event.stopPropagation();
            handleClick(row);
        });

        button.addEventListener('dblclick', (event) => {
            event.stopPropagation();
            handleDoubleClick(button, row);
        });

        return button;
    }

    function updateButton(row, button) {
        const timeElement = row.querySelector('td.updated time');
        const currentDatetime = timeElement ? timeElement.getAttribute('datetime') : null;
        const issueKey = getIssueKey(row);
        const storedData = rowData[issueKey];
        if (storedData) {
            button.textContent = storedData.clicked ? '已处理' : '未处理';
            button.style.backgroundColor = storedData.clicked ? '#28a745' : '#343a40';
        } else {
            button.textContent = '未处理';
            button.style.backgroundColor = '#343a40';
        }
    }

    function handleClick(row) {
        const issueKey = getIssueKey(row);
        if (rowData[issueKey]?.clicked) return;

        rowData[issueKey] = {
            clicked: true,
            lastUpdated: row.querySelector('td.updated time').getAttribute('datetime')
        };
        saveRowData(rowData);
        updateRow(row); // Ensure the button state is updated immediately after click
    }

    function handleDoubleClick(button, row) {
        const issueKey = getIssueKey(row);
        if (rowData[issueKey]?.clicked) {
            delete rowData[issueKey];
            saveRowData(rowData);
            button.textContent = '未处理';
            button.style.backgroundColor = '#343a40';
        }
    }

    function updateRow(row) {
        const timeElement = row.querySelector('td.updated time');
        if (timeElement) {
            const currentDatetime = timeElement.getAttribute('datetime');
            const issueKey = getIssueKey(row);
            const storedData = rowData[issueKey];

            if (storedData && storedData.lastUpdated !== currentDatetime) {
                rowData[issueKey] = { clicked: false, lastUpdated: currentDatetime };
                saveRowData(rowData);
            }

            const markButton = row.querySelector('td.priority button');
            if (markButton) {
                updateButton(row, markButton);
            }
        }
    }

    function formatUpdatedTime() {
        const now = new Date();
        document.querySelectorAll('td.updated time[datetime]').forEach(timeElement => {
            if (timeElement.textContent.includes('(')) return;

            const datetime = timeElement.getAttribute('datetime');
            const [date, time] = datetime.split('T');
            const formattedTime = `${date} ${time.split('+')[0]}`;
            const timeDate = new Date(datetime);
            const timeDiff = Math.floor((now - timeDate) / 1000); // Time difference in seconds
            let displayTimeDiff = '';

            if (timeDiff < 3600) { // Less than an hour
                displayTimeDiff = `${Math.floor(timeDiff / 60)} 分钟前`;
            } else if (timeDiff < 86400) { // Less than a day
                displayTimeDiff = `${Math.floor(timeDiff / 3600)} 小时前`;
            } else { // More than a day
                displayTimeDiff = `${Math.floor(timeDiff / 86400)} 天前`;
            }

            timeElement.setAttribute('title', `${formattedTime} (${displayTimeDiff})`);
            timeElement.textContent = `${formattedTime} (${displayTimeDiff})`;
        });
    }

    function getIssueKey(row) {
        const issueKeyElement = row.querySelector('td.issuekey a');
        return issueKeyElement ? issueKeyElement.textContent.trim() : null;
    }

    function copySummaryContent(row) {
        const summaryCell = row.querySelector('td.summary');
        if (summaryCell) {
            const content = summaryCell.textContent.trim();
            copyToClipboard(content);
            showNotification('内容已复制到剪贴板!', '#28a745');
        }
    }

    function initializeButtons() {
        document.querySelectorAll('tr').forEach(row => {
            const issueLinks = row.querySelectorAll('a.issue-link');
            if (issueLinks.length >= 2) {
                const secondLink = issueLinks[1];
                if (secondLink && (!secondLink.nextSibling || secondLink.nextSibling.tagName !== 'BUTTON')) {
                    const copyButton = createCopyButton(secondLink, row);
                    secondLink.parentNode.insertBefore(copyButton, secondLink.nextSibling);
                }
            }

            const issueKey = getIssueKey(row);
            if (issueKey) {
                const priorityCell = row.querySelector('td.priority');
                if (priorityCell) {
                    const existingButton = priorityCell.querySelector('button');
                    if (!existingButton) {
                        const markButton = createMarkButton(row);
                        priorityCell.appendChild(markButton);
                    } else {
                        updateRow(row);
                    }
                }
            }
        });
    }

    function getRowData() {
        const data = JSON.parse(localStorage.getItem('rowData')) || {};
        return data;
    }

    function saveRowData(data) {
        localStorage.setItem('rowData', JSON.stringify(data));
    }
        // 初始化函数
    function initializeLinks() {
        document.querySelectorAll('td.summary a.issue-link').forEach(link => {
            link.addEventListener('click', (event) => {
                // 取消默认的点击行为
                event.preventDefault();
                // 在新选项卡中打开链接
                window.open(link.href, '_blank');
            });

        });
    }

    const rowData = getRowData();

    formatUpdatedTime();
    initializeButtons();
    initializeLinks();

    const observer = new MutationObserver(() => {
        formatUpdatedTime();
        initializeButtons();
        updateColumnHeaders();
        initializeLinks();
        //incrementCount();
        highlightCurrentUser();
    });

    observer.observe(document.body, { childList: true, subtree: true });

    updateColumnHeaders();

    // 监听关键词变化并更新高亮显示
    window.addEventListener('callScriptB', (event) => {
        highlightCurrentUser();
    });
})();

