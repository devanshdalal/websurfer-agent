JSQ_DOCUMENT_ENHANCE_INPUT = """
() => {
    const elements = document.querySelectorAll('input, textarea, select');
    for (let e of elements) {
        e.style.border = '1px solid green';
    }
}
"""

JSQ_DOCUMENT_ENHANCE_LINKS = """
() => {
    function isElementVisible(el) {
        if (!el) return false; // Element does not exist

        function isStyleVisible(el) {
            const style = window.getComputedStyle(el);
            return style.width !== '0' &&
                   style.height !== '0' &&
                   style.opacity !== '0' &&
                   style.display !== 'none' &&
                   style.visibility !== 'hidden';
        }

        function isElementInViewport(el) {
            const rect = el.getBoundingClientRect();
            return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        }

        // Check if the element is visible style-wise
        if (!isStyleVisible(el)) {
            return false;
        }

        // Traverse up the DOM and check if any ancestor element is hidden
        let parent = el;
        while (parent) {
            if (!isStyleVisible(parent)) {
            return false;
            }
            parent = parent.parentElement;
        }

        // Finally, check if the element is within the viewport
        return isElementInViewport(el);
    }
    
    const elements = document.querySelectorAll('a, button, [role=button], [role=treeitem]');
    for (let e of elements) {
        const position = e.getBoundingClientRect();

        if( position.width > 5 && position.height > 5 && isElementVisible(e) ) {
            const link_text = e.textContent.replace(/[^a-zA-Z0-9 ]/g, '');
            e.style.border = '1px solid blue';
            e.setAttribute( "gpt-link-text", link_text );
        }
        ;
    }
}
"""

JSQ_GPT_ATTR_REMOVE = """
() => {
    document.querySelectorAll('[gpt-link-text]').forEach(e => {
        e.removeAttribute("gpt-link-text");
    });
}
"""

JSQ_GET_ELEMENT_ATTRIBUTES = """
(el, whitelist) => {
    return Object.fromEntries(Array.from(el.attributes)
        .filter(attr => whitelist.includes(attr.name) && attr.value.length > 0)
        .map(attr => [attr.name, attr.value]))
}
"""
