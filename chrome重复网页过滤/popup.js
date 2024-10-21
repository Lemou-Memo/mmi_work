document.addEventListener('DOMContentLoaded', function () {
  const toggle = document.getElementById('toggle');

  // 从 Chrome 的存储中获取开关状态
  chrome.storage.sync.get(['enabled'], function (result) {
    toggle.checked = result.enabled ?? true; // 默认为启用
  });

  // 监听开关的变化并保存状态
  toggle.addEventListener('change', function () {
    chrome.storage.sync.set({ enabled: toggle.checked }, function () {
      console.log('重复标签检测功能: ' + (toggle.checked ? '启用' : '禁用'));
    });
  });
});
