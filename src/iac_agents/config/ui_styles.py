"""UI styling configuration for Streamlit interface."""

# Main CSS styles for the application
MAIN_CSS = """
<style>
/* Main container styling */
.main-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2rem;
}

/* Chat container with proper scrolling */
.chat-container {
    height: 600px;
    overflow-y: auto;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 1rem;
    background-color: #fafafa;
    margin-bottom: 1rem;
}

/* Auto-scroll to bottom for new messages */
.element-container:last-child {
    margin-bottom: 0;
}

/* Chat input spacing */
.stChatInput {
    margin-left: 1rem;
    margin-top: 1rem;
    margin-bottom: 1rem;
}

.stChatInput > div {
    margin-left: 1rem;
}

/* Agent status indicators - Fixed styling */
.agent-status {
    display: flex;
    flex-direction: column;
    margin: 0.5rem 0;
    padding: 0.75rem;
    border-radius: 8px;
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    transition: all 0.2s ease;
}

.agent-status:hover {
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.agent-status.active {
    background-color: #d4edda;
    border-color: #28a745;
    border-left: 4px solid #28a745;
}

.agent-status.working {
    background-color: #fff3cd;
    border-color: #ffc107;
    border-left: 4px solid #ffc107;
    animation: pulse 2s infinite;
}

.agent-status.idle {
    background-color: #f8f9fa;
    border-color: #6c757d;
    color: #6c757d;
}

.agent-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: bold;
    font-size: 0.9rem;
}

.agent-subtext {
    font-size: 0.8rem;
    margin-top: 0.25rem;
    opacity: 0.8;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}

/* Progress indicators */
.workflow-stage {
    display: flex;
    align-items: center;
    margin: 0.25rem 0;
    font-size: 0.9rem;
    padding: 0.25rem 0;
}

.workflow-stage.completed {
    color: #28a745;
    font-weight: 500;
}

.workflow-stage.current {
    color: #ffc107;
    font-weight: bold;
    background-color: #fff8dc;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
}

.workflow-stage.pending {
    color: #6c757d;
}

/* Logo styling */
.logo-container {
    display: flex;
    align-items: center;
    gap: 1rem;
}

/* Cost estimation styling */
.cost-estimate {
    background-color: #e3f2fd;
    border-left: 4px solid #2196f3;
    padding: 1rem;
    border-radius: 5px;
    margin: 1rem 0;
}

/* Activity log styling - Fixed */
.activity-log {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 0.75rem;
    max-height: 250px;
    overflow-y: auto;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 0.75rem;
    line-height: 1.4;
}

.activity-entry {
    margin-bottom: 0.5rem;
    padding: 0.25rem 0;
    border-bottom: 1px solid #e9ecef;
}

.activity-entry:last-child {
    border-bottom: none;
    margin-bottom: 0;
}

.activity-timestamp {
    color: #6c757d;
    font-weight: 500;
}

.activity-agent {
    color: #495057;
    font-weight: 600;
}

.activity-message {
    color: #343a40;
    margin-top: 0.1rem;
}

/* Sidebar sections */
.sidebar-section {
    background-color: #ffffff;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    border: 1px solid #e9ecef;
}

.sidebar-section h3 {
    margin-top: 0;
    margin-bottom: 0.75rem;
    color: #495057;
    border-bottom: 2px solid #e9ecef;
    padding-bottom: 0.5rem;
}

/* System metrics styling */
.metric-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    margin: 0.25rem 0;
}

.metric-label {
    font-size: 0.8rem;
    color: #6c757d;
}

.metric-value {
    font-size: 1.1rem;
    font-weight: bold;
    color: #495057;
}

/* Chat container styling for better scrolling */
.chat-container {
    height: 70vh;
    overflow-y: auto;
    scroll-behavior: smooth;
}

/* Force smooth scrolling on main content */
section[data-testid="stMain"] {
    scroll-behavior: smooth;
}

/* Chat message container improvements */
[data-testid="stChatMessage"] {
    scroll-margin-bottom: 20px;
}

/* Input spacing fix */
.stChatInput > div {
    margin-left: 1rem;
}
</style>
"""

# Auto-scroll JavaScript template - More robust implementation
AUTO_SCROLL_JS = """
<script>
function scrollToBottom() {{
    // Try multiple strategies to find the chat container
    var attempts = [
        function() {{ return parent.document.querySelector('[data-testid="stChatMessage"]'); }},
        function() {{ return parent.document.querySelector('[data-testid="stVerticalBlock"]'); }},
        function() {{ return parent.document.querySelector('[data-testid="stMainBlockContainer"]'); }},
        function() {{ return parent.document.querySelector('section[data-testid="stMain"]'); }}
    ];
    
    var container = null;
    for (var i = 0; i < attempts.length; i++) {{
        try {{
            container = attempts[i]();
            if (container) break;
        }} catch(e) {{
            continue;
        }}
    }}
    
    if (container) {{
        // Find all chat messages
        var chatMessages = parent.document.querySelectorAll('[data-testid="stChatMessage"]');
        if (chatMessages.length > 0) {{
            // Scroll to the last message
            var lastMessage = chatMessages[chatMessages.length - 1];
            lastMessage.scrollIntoView({{ behavior: 'smooth', block: 'end', inline: 'nearest' }});
            return true;
        }}
        
        // Fallback: scroll the main container to bottom
        try {{
            var mainContainer = parent.document.querySelector('section[data-testid="stMain"]');
            if (mainContainer) {{
                mainContainer.scrollTop = mainContainer.scrollHeight;
                return true;
            }}
        }} catch(e) {{
            // Ignore
        }}
    }}
    
    // Final fallback: scroll window
    try {{
        parent.window.scrollTo({{ top: parent.document.body.scrollHeight, behavior: 'smooth' }});
    }} catch(e) {{
        // Ignore
    }}
    
    return false;
}}

// Multiple scroll attempts with increasing delays
setTimeout(scrollToBottom, 100);
setTimeout(scrollToBottom, 300);
setTimeout(scrollToBottom, 500);

// Also try after DOM mutations (when content changes)
if (parent.MutationObserver) {{
    var observer = new parent.MutationObserver(function(mutations) {{
        var shouldScroll = false;
        mutations.forEach(function(mutation) {{
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {{
                for (var i = 0; i < mutation.addedNodes.length; i++) {{
                    var node = mutation.addedNodes[i];
                    if (node.nodeType === 1 && 
                        (node.getAttribute('data-testid') === 'stChatMessage' ||
                         node.querySelector && node.querySelector('[data-testid="stChatMessage"]'))) {{
                        shouldScroll = true;
                        break;
                    }}
                }}
            }}
        }});
        
        if (shouldScroll) {{
            setTimeout(scrollToBottom, 50);
        }}
    }});
    
    var targetNode = parent.document.querySelector('section[data-testid="stMain"]');
    if (targetNode) {{
        observer.observe(targetNode, {{
            childList: true,
            subtree: true
        }});
        
        // Stop observing after 10 seconds to prevent memory leaks
        setTimeout(function() {{
            observer.disconnect();
        }}, 10000);
    }}
}}
</script>
"""

# Sidebar section template
SIDEBAR_SECTION_TEMPLATE = """
<div class="sidebar-section">
    <h3>{title}</h3>
    {content}
</div>
"""

# Agent status template
AGENT_STATUS_TEMPLATE = """
<div class="agent-status {status_class}">
    <div class="agent-header">
        {emoji} {agent_name}
    </div>
    <div class="agent-subtext">
        {status_text} - {subtext}
    </div>
</div>
"""

# Activity entry template
ACTIVITY_ENTRY_TEMPLATE = """
<div class="activity-entry">
    <div class="activity-timestamp">[{timestamp}]</div>
    <div class="activity-agent">{agent_name}</div>
    <div class="activity-message">{activity_message}</div>
</div>
"""

# Metric container template
METRIC_CONTAINER_TEMPLATE = """
<div class="metric-container">
    <span class="metric-label">{label}</span>
    <span class="metric-value">{value}</span>
</div>
"""