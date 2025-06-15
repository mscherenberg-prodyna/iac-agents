function scrollToBottom() {
    // Try multiple strategies to find the chat container
    var attempts = [
        function() { return parent.document.querySelector('[data-testid="stChatMessage"]'); },
        function() { return parent.document.querySelector('[data-testid="stVerticalBlock"]'); },
        function() { return parent.document.querySelector('[data-testid="stMainBlockContainer"]'); },
        function() { return parent.document.querySelector('section[data-testid="stMain"]'); }
    ];
    
    var container = null;
    for (var i = 0; i < attempts.length; i++) {
        try {
            container = attempts[i]();
            if (container) break;
        } catch(e) {
            continue;
        }
    }
    
    if (container) {
        // Find all chat messages
        var chatMessages = parent.document.querySelectorAll('[data-testid="stChatMessage"]');
        if (chatMessages.length > 0) {
            // Scroll to the last message
            var lastMessage = chatMessages[chatMessages.length - 1];
            lastMessage.scrollIntoView({ behavior: 'smooth', block: 'end', inline: 'nearest' });
            return true;
        }
        
        // Fallback: scroll the main container to bottom
        try {
            var mainContainer = parent.document.querySelector('section[data-testid="stMain"]');
            if (mainContainer) {
                mainContainer.scrollTop = mainContainer.scrollHeight;
                return true;
            }
        } catch(e) {
            // Ignore
        }
    }
    
    // Final fallback: scroll window
    try {
        parent.window.scrollTo({ top: parent.document.body.scrollHeight, behavior: 'smooth' });
    } catch(e) {
        // Ignore
    }
    
    return false;
}

// Multiple scroll attempts with increasing delays
setTimeout(scrollToBottom, 100);
setTimeout(scrollToBottom, 300);
setTimeout(scrollToBottom, 500);

// Also try after DOM mutations (when content changes)
if (parent.MutationObserver) {
    var observer = new parent.MutationObserver(function(mutations) {
        var shouldScroll = false;
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                for (var i = 0; i < mutation.addedNodes.length; i++) {
                    var node = mutation.addedNodes[i];
                    if (node.nodeType === 1 && 
                        (node.getAttribute('data-testid') === 'stChatMessage' ||
                         node.querySelector && node.querySelector('[data-testid="stChatMessage"]'))) {
                        shouldScroll = true;
                        break;
                    }
                }
            }
        });
        
        if (shouldScroll) {
            setTimeout(scrollToBottom, 50);
        }
    });
    
    var targetNode = parent.document.querySelector('section[data-testid="stMain"]');
    if (targetNode) {
        observer.observe(targetNode, {
            childList: true,
            subtree: true
        });
        
        // Stop observing after 10 seconds to prevent memory leaks
        setTimeout(function() {
            observer.disconnect();
        }, 10000);
    }
}