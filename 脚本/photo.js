// ==UserScript==
// @name         获取所有图片和视频显示右下角翻页
// @namespace    http://tampermonkey.net/
// @version      2.1
// @description  自动在浏览器中播放媒体链接，右下角显示浮动画廊，支持全屏，图像居中显示
// @author       jiale.pan
// @match        http://jira-ex.transsion.com/browse/*
// @icon         data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==
// @grant        none
// @updateURL    https://raw.githubusercontent.com/Lemou-Memo/mmi_work/refs/heads/master/%E8%84%9A%E6%9C%AC/photo.js
// @downloadURL  https://raw.githubusercontent.com/Lemou-Memo/mmi_work/refs/heads/master/%E8%84%9A%E6%9C%AC/photo.js
// ==/UserScript==
(function() {
    'use strict';

    // 创建浮动画廊容器ceshi
    const galleryContainer = document.createElement('div');
    galleryContainer.style.position = 'fixed';
    galleryContainer.style.bottom = '20px';
    galleryContainer.style.right = '20px';
    galleryContainer.style.width = '350px';
    galleryContainer.style.height = '600px'; // 增加高度
    galleryContainer.style.overflow = 'hidden';
    galleryContainer.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    galleryContainer.style.color = 'white';
    galleryContainer.style.borderRadius = '10px';
    galleryContainer.style.display = 'flex';
    galleryContainer.style.flexDirection = 'column';
    galleryContainer.style.alignItems = 'center';
    galleryContainer.style.justifyContent = 'center';
    galleryContainer.style.zIndex = '1000';
    galleryContainer.style.padding = '10px'; // 添加内边距
    galleryContainer.style.boxSizing = 'border-box';
    galleryContainer.style.opacity = '1'; // 确保初始透明度设置为1
    galleryContainer.style.transition = 'opacity 0.5s'; // 隐藏/显示的平滑过渡
    galleryContainer.style.visibility = 'hidden'; // 初始状态为隐藏
    document.body.appendChild(galleryContainer);

    // 创建按钮的顶部栏
    const topBar = document.createElement('div');
    topBar.style.width = '100%';
    topBar.style.position = 'absolute';
    topBar.style.top = '0';
    topBar.style.left = '0';
    topBar.style.display = 'flex';
    topBar.style.justifyContent = 'space-between';
    topBar.style.padding = '5px';
    topBar.style.boxSizing = 'border-box';
    galleryContainer.appendChild(topBar);

    // 创建上一页按钮
    const prevButton = document.createElement('button');
    prevButton.textContent = '<';
    prevButton.style.backgroundColor = 'rgba(255, 255, 255, 0.5)';
    prevButton.style.border = 'none';
    prevButton.style.color = 'black';
    prevButton.style.borderRadius = '5px';
    prevButton.style.cursor = 'pointer';
    prevButton.style.zIndex = '1001'; // 确保按钮在所有元素之上
    topBar.appendChild(prevButton);

    // 创建关闭按钮
    const closeButton = document.createElement('button');
    closeButton.textContent = 'X';
    closeButton.style.backgroundColor = 'rgba(255, 0, 0, 0.5)';
    closeButton.style.border = 'none';
    closeButton.style.color = 'white';
    closeButton.style.borderRadius = '5px';
    closeButton.style.cursor = 'pointer';
    closeButton.style.zIndex = '1001'; // 确保按钮在所有元素之上
    closeButton.style.margin = '0 10px'; // 按钮之间的间距
    topBar.appendChild(closeButton);

    // 创建下一页按钮
    const nextButton = document.createElement('button');
    nextButton.textContent = '>';
    nextButton.style.backgroundColor = 'rgba(255, 255, 255, 0.5)';
    nextButton.style.border = 'none';
    nextButton.style.color = 'black';
    nextButton.style.borderRadius = '5px';
    nextButton.style.cursor = 'pointer';
    nextButton.style.zIndex = '1001'; // 确保按钮在所有元素之上
    topBar.appendChild(nextButton);

    // 创建媒体项容器
    const mediaContainer = document.createElement('div');
    mediaContainer.style.width = '100%';
    mediaContainer.style.height = '100%';
    mediaContainer.style.display = 'flex';
    mediaContainer.style.alignItems = 'center';   // 垂直居中
    mediaContainer.style.justifyContent = 'center'; // 水平居中
    galleryContainer.appendChild(mediaContainer);

    // 存储所有媒体项
    const mediaItems = [];
    let currentIndex = 0;

    // 显示当前媒体项的函数
    function showCurrentMedia() {
        mediaItems.forEach((media, index) => {
            media.style.display = index === currentIndex ? 'block' : 'none';
        });
    }

    // 查找页面上的所有链接
    const links = document.querySelectorAll('a');

    links.forEach(link => {
        const href = link.href.toLowerCase();  // 转换为小写以便于比较

        // 检查链接是否为MP4文件
        if (href.endsWith('.mp4')) {
            // 创建视频元素
            const video = document.createElement('video');
            video.controls = true;
            video.src = href;
            video.style.maxWidth = '100%';
            video.style.maxHeight = '100%';
            video.style.cursor = 'pointer';
            video.style.display = 'none';

            // 视频的全屏支持
            video.addEventListener('click', (e) => {
                e.preventDefault();
                if (video.requestFullscreen) {
                    video.requestFullscreen();
                } else if (video.webkitRequestFullscreen) { // Safari
                    video.webkitRequestFullscreen();
                } else if (video.msRequestFullscreen) { // IE11
                    video.msRequestFullscreen();
                }
            });

            mediaItems.push(video);
            mediaContainer.appendChild(video);
        }
        // 检查链接是否为图片文件（PNG, JPG, JPEG, WEBP）
        else if (href.endsWith('.png') || href.endsWith('.jpg') || href.endsWith('.jpeg') || href.endsWith('.webp')) {
            // 创建图片元素
            const img = document.createElement('img');
            img.src = href;
            img.style.maxWidth = '100%';
            img.style.maxHeight = '100%';
            img.style.cursor = 'pointer';
            img.style.display = 'none';

            // 添加全屏支持的事件监听器
            img.addEventListener('click', (e) => {
                e.preventDefault();
                if (img.requestFullscreen) {
                    img.requestFullscreen();
                } else if (img.webkitRequestFullscreen) { // Safari
                    img.webkitRequestFullscreen();
                } else if (img.msRequestFullscreen) { // IE11
                    img.msRequestFullscreen();
                }
            });

            mediaItems.push(img);
            mediaContainer.appendChild(img);
        }
    });

    // 如果有媒体项则显示画廊
    if (mediaItems.length > 0) {
        galleryContainer.style.visibility = 'visible'; // 使画廊可见
        showCurrentMedia(); // 显示第一个媒体项
    } else {
        // 如果没有找到媒体项，则隐藏画廊容器
        galleryContainer.style.display = 'none';
    }

    // 为按钮添加事件监听器
    prevButton.addEventListener('click', () => {
        if (mediaItems.length > 0) {
            currentIndex = (currentIndex > 0) ? currentIndex - 1 : mediaItems.length - 1;
            showCurrentMedia();
        }
    });

    nextButton.addEventListener('click', () => {
        if (mediaItems.length > 0) {
            currentIndex = (currentIndex < mediaItems.length - 1) ? currentIndex + 1 : 0;
            showCurrentMedia();
        }
    });

    // 为关闭按钮添加事件监听器
    closeButton.addEventListener('click', () => {
        galleryContainer.style.visibility = 'hidden'; // 隐藏画廊

        // 停止所有视频播放并静音
        mediaItems.forEach(media => {
            if (media.tagName === 'VIDEO') {
                media.pause(); // 暂停视频
                media.currentTime = 0; // 重置播放时间
                media.volume = 0; // 静音
            }
        });
    });
})();
