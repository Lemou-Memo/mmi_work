// 检测用户手动输入或者导航的网页
chrome.webNavigation.onCommitted.addListener(function(details) {
    const tabId = details.tabId;
    const newUrl = details.url;
  
    // 读取存储中的开关状态，确认功能是否启用
    chrome.storage.sync.get(['enabled'], function(result) {
      if (result.enabled) {
        // 获取所有打开的选项卡
        chrome.tabs.query({}, function(tabs) {
          let duplicateTab = null;
  
          // 检查是否已经存在相同的 URL
          for (let existingTab of tabs) {
            if (existingTab.url === newUrl && existingTab.id !== tabId) {
              duplicateTab = existingTab;
              break;
            }
          }
  
          // 如果找到重复的选项卡
          if (duplicateTab) {
            // 切换到已有的选项卡
            chrome.tabs.update(duplicateTab.id, { active: true });
  
            // 关闭当前的重复选项卡
            chrome.tabs.remove(tabId);
          }
        });
      } else {
        console.log('重复标签检测已禁用');
      }
    });
  });
  