
# Streamlit Example for EchoScan Excitement Layer

import streamlit as st
import json
from excitement_layer import generate_excitement_triggers

def display_echoscan_results(result):
    '''Display EchoScan results with excitement layer'''
    
    # Generate excitement triggers
    excitement_data = generate_excitement_triggers(
        result.get('verdict', 'Unknown'),
        result.get('confidence', 0.5),
        result.get('echo_sense', 0.5)
    )
    
    # Create columns for better layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display main results
        verdict_color = {
            'Authentic': 'green',
            'Plausible': 'orange', 
            'Hallucination': 'red'
        }.get(result.get('verdict'), 'blue')
        
        st.markdown(f"## EchoScan Analysis Result")
        st.markdown(f"**Verdict:** :{verdict_color}[{result.get('verdict', 'Unknown')}]")
        st.metric("Confidence", f"{result.get('confidence', 0) * 100:.1f}%")
        st.metric("EchoSense Score", f"{result.get('echo_sense', 0) * 100:.1f}%") 
        st.metric("Delta S", f"{result.get('delta_s', 0):.5f}")
        st.text(f"Glyph ID: {result.get('glyph_id', 'Unknown')}")
    
    with col2:
        # Excitement controls
        st.markdown("### 🎉 Excitement Layer")
        if excitement_data.get('excitement_enabled'):
            st.success("Excitement effects enabled!")
            
            # Show what effects would trigger
            for trigger in excitement_data.get('triggers', []):
                st.write(f"- {trigger['type'].title()}: {trigger.get('message', '')}")
        else:
            st.info("Excitement effects disabled")
    
    # Inject JavaScript for excitement effects
    if excitement_data.get('excitement_enabled'):
        excitement_js = f'''
        <script>
        // Inject excitement data and trigger effects
        window.echoScanExcitementData = {json.dumps(excitement_data)};
        
        // Load excitement layer if not already loaded
        if (!window.echoScanExcitement) {{
            // You would load the JavaScript here
            console.log('Loading EchoScan Excitement Layer...');
        }} else {{
            // Trigger excitement effects
            window.echoScanExcitement.trigger(window.echoScanExcitementData);
        }}
        </script>
        '''
        
        st.components.v1.html(excitement_js, height=0)

# Example usage in main Streamlit app:
# 
# st.title("EchoScan Demo with Excitement Layer")
# 
# input_text = st.text_area("Enter text to analyze:")
# if st.button("Analyze"):
#     # Run EchoScan analysis (placeholder)
#     result = {
#         'verdict': 'Authentic',
#         'confidence': 0.85,
#         'echo_sense': 0.78,
#         'delta_s': 0.00123,
#         'glyph_id': 'GHX-ABC123'
#     }
#     
#     display_echoscan_results(result)
