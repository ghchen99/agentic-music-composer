"""
Music theory helper functions
"""

def syllabify(text):
    """Simple syllable counter - splits text into approximate syllables"""
    if not text:
        return []
        
    # Remove punctuation except apostrophes
    import re
    text = re.sub(r'[^\w\s\']', '', text)
    
    # Split into words
    words = text.split()
    
    syllables = []
    for word in words:
        # Count vowel sequences as syllables
        vowels = "aeiouy"
        count = 0
        in_vowel_group = False
        
        for char in word.lower():
            if char in vowels:
                if not in_vowel_group:
                    count += 1
                    in_vowel_group = True
            else:
                in_vowel_group = False
        
        # Ensure at least one syllable per word
        if count == 0:
            count = 1
            
        # Add each syllable to the list
        for i in range(count):
            syllables.append(word if count == 1 else f"{word}_{i+1}")
    
    return syllables