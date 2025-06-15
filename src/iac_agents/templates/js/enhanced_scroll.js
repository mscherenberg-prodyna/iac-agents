// Enhanced autoscroll with multiple strategies
function enhancedScrollToBottom(scrollTargetKey) {
    var scrolled = false;

    // Strategy 1: Scroll to our target element
    try {
        var target = parent.document.getElementById(scrollTargetKey);
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'end' });
            scrolled = true;
        }
    } catch(e) {
        console.log('Target element scroll failed:', e);
    }

    // Strategy 2: Original chat message scrolling
    if (!scrolled) {
        try {
            var chatMessages = parent.document.querySelectorAll('[data-testid="stChatMessage"]');
            if (chatMessages.length > 0) {
                var lastMessage = chatMessages[chatMessages.length - 1];
                lastMessage.scrollIntoView({ behavior: 'smooth', block: 'end' });
                scrolled = true;
            }
        } catch(e) {
            console.log('Chat message scroll failed:', e);
        }
    }

    // Strategy 3: Scroll main container
    if (!scrolled) {
        try {
            var mainContainer = parent.document.querySelector('section[data-testid="stMain"]');
            if (mainContainer) {
                mainContainer.scrollTop = mainContainer.scrollHeight;
                scrolled = true;
            }
        } catch(e) {
            console.log('Main container scroll failed:', e);
        }
    }

    // Strategy 4: Window scroll
    if (!scrolled) {
        try {
            parent.window.scrollTo(0, parent.document.body.scrollHeight);
        } catch(e) {
            console.log('Window scroll failed:', e);
        }
    }

    return scrolled;
}

// Execute with multiple timing attempts
function setupEnhancedScroll(scrollTargetKey) {
    setTimeout(function() { enhancedScrollToBottom(scrollTargetKey); }, 50);
    setTimeout(function() { enhancedScrollToBottom(scrollTargetKey); }, 200);
    setTimeout(function() { enhancedScrollToBottom(scrollTargetKey); }, 500);
    setTimeout(function() { enhancedScrollToBottom(scrollTargetKey); }, 1000);
}