"""
UI Excitement Layer - Confetti, Balloons, and Fireworks for EchoScan
Provides engaging visual feedback for verdict results
"""

import os
import json
from typing import Dict, Any, List, Optional

class UIExcitementConfig:
    """Configuration for UI excitement features"""
    
    def __init__(self):
        self.enabled = os.getenv('UI_EXCITEMENT_ENABLED', 'true').lower() == 'true'
        self.confetti_enabled = os.getenv('UI_CONFETTI_ENABLED', 'true').lower() == 'true'
        self.balloons_enabled = os.getenv('UI_BALLOONS_ENABLED', 'true').lower() == 'true'
        self.fireworks_enabled = os.getenv('UI_FIREWORKS_ENABLED', 'true').lower() == 'true'

def generate_excitement_triggers(verdict: str, confidence: float, echo_sense: float) -> Dict[str, Any]:
    """Generate excitement triggers based on EchoScan results"""
    
    config = UIExcitementConfig()
    
    if not config.enabled:
        return {'excitement_enabled': False}
    
    triggers = {
        'excitement_enabled': True,
        'verdict': verdict,
        'confidence': confidence,
        'echo_sense': echo_sense,
        'triggers': []
    }
    
    # Determine excitement level based on verdict and confidence
    if verdict == 'Authentic' and confidence > 0.8:
        # High confidence authentic - celebrate!
        if config.confetti_enabled:
            triggers['triggers'].append({
                'type': 'confetti',
                'intensity': 'high',
                'colors': ['#00FF00', '#00CC00', '#32CD32', '#90EE90'],
                'duration': 3000,
                'message': '🎉 Authentic Content Verified! 🎉'
            })
        
        if config.fireworks_enabled:
            triggers['triggers'].append({
                'type': 'fireworks',
                'pattern': 'burst',
                'colors': ['gold', 'green', 'white'],
                'count': 3,
                'message': '✨ Authenticity Confirmed! ✨'
            })
    
    elif verdict == 'Authentic' and confidence > 0.6:
        # Moderate confidence authentic
        if config.balloons_enabled:
            triggers['triggers'].append({
                'type': 'balloons',
                'count': 5,
                'colors': ['#90EE90', '#98FB98', '#00FF7F'],
                'animation': 'float_up',
                'duration': 2500,
                'message': '🎈 Content Appears Authentic 🎈'
            })
    
    elif verdict == 'Plausible':
        # Neutral result - subtle celebration
        if config.balloons_enabled:
            triggers['triggers'].append({
                'type': 'balloons',
                'count': 3,
                'colors': ['#FFD700', '#FFA500', '#FFFF00'],
                'animation': 'gentle_sway',
                'duration': 2000,
                'message': '⚖️ Plausible Content Detected'
            })
    
    elif verdict == 'Hallucination' and confidence > 0.7:
        # High confidence detection - alert celebration
        if config.confetti_enabled:
            triggers['triggers'].append({
                'type': 'confetti',
                'intensity': 'medium',
                'colors': ['#FF4500', '#FF6347', '#FFA500'],
                'duration': 2000,
                'message': '🚨 AI Generation Detected! 🚨'
            })
        
        if config.fireworks_enabled:
            triggers['triggers'].append({
                'type': 'fireworks',
                'pattern': 'warning',
                'colors': ['red', 'orange', 'yellow'],
                'count': 2,
                'message': '⚠️ Potential AI Content Found!'
            })
    
    # Add echo_sense bonus effects
    if echo_sense > 0.9:
        triggers['triggers'].append({
            'type': 'sparkles',
            'intensity': 'high',
            'colors': ['#FFD700', '#FFFFFF', '#87CEEB'],
            'duration': 1500,
            'message': '⭐ Exceptional EchoSense Score! ⭐'
        })
    
    return triggers

def generate_javascript_excitement() -> str:
    """Generate JavaScript code for excitement effects"""
    
    return """
// EchoScan Excitement Layer JavaScript
class EchoScanExcitement {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.balloons = [];
        this.isAnimating = false;
    }
    
    initCanvas() {
        // Create canvas if it doesn't exist
        this.canvas = document.getElementById('echoscan-excitement-canvas');
        if (!this.canvas) {
            this.canvas = document.createElement('canvas');
            this.canvas.id = 'echoscan-excitement-canvas';
            this.canvas.style.position = 'fixed';
            this.canvas.style.top = '0';
            this.canvas.style.left = '0';
            this.canvas.style.width = '100%';
            this.canvas.style.height = '100%';
            this.canvas.style.pointerEvents = 'none';
            this.canvas.style.zIndex = '9999';
            document.body.appendChild(this.canvas);
        }
        
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.ctx = this.canvas.getContext('2d');
    }
    
    triggerConfetti(config) {
        this.initCanvas();
        
        const particleCount = config.intensity === 'high' ? 150 : 
                            config.intensity === 'medium' ? 100 : 50;
        
        for (let i = 0; i < particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: -10,
                vx: (Math.random() - 0.5) * 4,
                vy: Math.random() * 3 + 1,
                color: config.colors[Math.floor(Math.random() * config.colors.length)],
                size: Math.random() * 4 + 2,
                rotation: Math.random() * 360,
                rotationSpeed: (Math.random() - 0.5) * 10,
                life: 1.0
            });
        }
        
        this.showMessage(config.message);
        this.animate();
        
        setTimeout(() => {
            this.fadeOut();
        }, config.duration || 3000);
    }
    
    triggerBalloons(config) {
        this.initCanvas();
        
        for (let i = 0; i < config.count; i++) {
            this.balloons.push({
                x: Math.random() * (this.canvas.width - 100) + 50,
                y: this.canvas.height + 50,
                vy: -2 - Math.random(),
                vx: (Math.random() - 0.5) * 2,
                color: config.colors[Math.floor(Math.random() * config.colors.length)],
                size: 30 + Math.random() * 20,
                bobOffset: Math.random() * Math.PI * 2,
                life: 1.0
            });
        }
        
        this.showMessage(config.message);
        this.animateBalloons();
        
        setTimeout(() => {
            this.fadeOut();
        }, config.duration || 2500);
    }
    
    triggerFireworks(config) {
        this.initCanvas();
        
        const launchPoints = [];
        for (let i = 0; i < config.count; i++) {
            launchPoints.push({
                x: Math.random() * this.canvas.width,
                y: this.canvas.height,
                targetY: Math.random() * this.canvas.height * 0.5 + 50
            });
        }
        
        this.launchFireworks(launchPoints, config);
        this.showMessage(config.message);
    }
    
    launchFireworks(launchPoints, config) {
        launchPoints.forEach((point, index) => {
            setTimeout(() => {
                // Launch rocket
                const rocket = {
                    x: point.x,
                    y: point.y,
                    targetY: point.targetY,
                    vy: -8,
                    color: config.colors[index % config.colors.length],
                    exploded: false
                };
                
                const animateRocket = () => {
                    this.ctx.fillStyle = rocket.color;
                    this.ctx.fillRect(rocket.x - 2, rocket.y - 10, 4, 10);
                    
                    rocket.y += rocket.vy;
                    
                    if (rocket.y <= rocket.targetY && !rocket.exploded) {
                        rocket.exploded = true;
                        this.explodeFirework(rocket.x, rocket.y, rocket.color);
                    } else if (!rocket.exploded) {
                        requestAnimationFrame(animateRocket);
                    }
                };
                
                this.initCanvas();
                animateRocket();
            }, index * 500);
        });
    }
    
    explodeFirework(x, y, baseColor) {
        const sparkCount = 30;
        const sparks = [];
        
        for (let i = 0; i < sparkCount; i++) {
            const angle = (Math.PI * 2 * i) / sparkCount;
            const velocity = Math.random() * 4 + 2;
            
            sparks.push({
                x: x,
                y: y,
                vx: Math.cos(angle) * velocity,
                vy: Math.sin(angle) * velocity,
                color: baseColor,
                life: 1.0,
                decay: 0.015 + Math.random() * 0.01
            });
        }
        
        const animateSparks = () => {
            this.ctx.globalCompositeOperation = 'source-over';
            
            sparks.forEach(spark => {
                if (spark.life > 0) {
                    this.ctx.globalAlpha = spark.life;
                    this.ctx.fillStyle = spark.color;
                    this.ctx.fillRect(spark.x - 1, spark.y - 1, 2, 2);
                    
                    spark.x += spark.vx;
                    spark.y += spark.vy;
                    spark.vy += 0.1; // gravity
                    spark.life -= spark.decay;
                }
            });
            
            this.ctx.globalAlpha = 1.0;
            
            if (sparks.some(spark => spark.life > 0)) {
                requestAnimationFrame(animateSparks);
            }
        };
        
        animateSparks();
    }
    
    animate() {
        if (!this.isAnimating) {
            this.isAnimating = true;
            this.animationLoop();
        }
    }
    
    animationLoop() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Animate confetti particles
        this.particles.forEach((particle, index) => {
            if (particle.life > 0) {
                this.ctx.save();
                this.ctx.translate(particle.x, particle.y);
                this.ctx.rotate(particle.rotation * Math.PI / 180);
                this.ctx.globalAlpha = particle.life;
                this.ctx.fillStyle = particle.color;
                this.ctx.fillRect(-particle.size/2, -particle.size/2, particle.size, particle.size);
                this.ctx.restore();
                
                particle.x += particle.vx;
                particle.y += particle.vy;
                particle.vy += 0.1; // gravity
                particle.rotation += particle.rotationSpeed;
                particle.life -= 0.005;
            } else {
                this.particles.splice(index, 1);
            }
        });
        
        if (this.particles.length > 0 || this.balloons.length > 0) {
            requestAnimationFrame(() => this.animationLoop());
        } else {
            this.isAnimating = false;
        }
    }
    
    animateBalloons() {
        if (!this.isAnimating) {
            this.isAnimating = true;
            this.balloonLoop();
        }
    }
    
    balloonLoop() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.balloons.forEach((balloon, index) => {
            if (balloon.life > 0 && balloon.y > -balloon.size) {
                // Draw balloon
                const bobAmount = Math.sin(Date.now() * 0.01 + balloon.bobOffset) * 2;
                
                this.ctx.globalAlpha = balloon.life;
                this.ctx.fillStyle = balloon.color;
                this.ctx.beginPath();
                this.ctx.arc(balloon.x + bobAmount, balloon.y, balloon.size, 0, Math.PI * 2);
                this.ctx.fill();
                
                // Draw string
                this.ctx.strokeStyle = '#333333';
                this.ctx.lineWidth = 1;
                this.ctx.beginPath();
                this.ctx.moveTo(balloon.x + bobAmount, balloon.y + balloon.size);
                this.ctx.lineTo(balloon.x + bobAmount, balloon.y + balloon.size + 30);
                this.ctx.stroke();
                
                // Update position
                balloon.x += balloon.vx;
                balloon.y += balloon.vy;
                balloon.life -= 0.002;
            } else {
                this.balloons.splice(index, 1);
            }
        });
        
        this.ctx.globalAlpha = 1.0;
        
        if (this.balloons.length > 0) {
            requestAnimationFrame(() => this.balloonLoop());
        } else {
            this.isAnimating = false;
        }
    }
    
    showMessage(message) {
        // Create or update message element
        let msgElement = document.getElementById('echoscan-excitement-message');
        if (!msgElement) {
            msgElement = document.createElement('div');
            msgElement.id = 'echoscan-excitement-message';
            msgElement.style.position = 'fixed';
            msgElement.style.top = '20%';
            msgElement.style.left = '50%';
            msgElement.style.transform = 'translateX(-50%)';
            msgElement.style.fontSize = '2em';
            msgElement.style.fontWeight = 'bold';
            msgElement.style.color = '#333';
            msgElement.style.textAlign = 'center';
            msgElement.style.zIndex = '10000';
            msgElement.style.pointerEvents = 'none';
            msgElement.style.textShadow = '2px 2px 4px rgba(0,0,0,0.3)';
            document.body.appendChild(msgElement);
        }
        
        msgElement.innerHTML = message;
        msgElement.style.opacity = '1';
        
        // Fade out message after 3 seconds
        setTimeout(() => {
            msgElement.style.transition = 'opacity 1s';
            msgElement.style.opacity = '0';
        }, 3000);
    }
    
    fadeOut() {
        if (this.canvas) {
            this.canvas.style.transition = 'opacity 1s';
            this.canvas.style.opacity = '0';
            setTimeout(() => {
                if (this.canvas && this.canvas.parentNode) {
                    this.canvas.parentNode.removeChild(this.canvas);
                }
                this.canvas = null;
                this.particles = [];
                this.balloons = [];
            }, 1000);
        }
    }
    
    // Main trigger function
    trigger(excitementData) {
        if (!excitementData.excitement_enabled) {
            return;
        }
        
        excitementData.triggers.forEach((trigger, index) => {
            setTimeout(() => {
                switch (trigger.type) {
                    case 'confetti':
                        this.triggerConfetti(trigger);
                        break;
                    case 'balloons':
                        this.triggerBalloons(trigger);
                        break;
                    case 'fireworks':
                        this.triggerFireworks(trigger);
                        break;
                    case 'sparkles':
                        // Simple sparkles implementation
                        this.triggerConfetti({
                            ...trigger,
                            intensity: 'low'
                        });
                        break;
                }
            }, index * 500); // Stagger effects
        });
    }
}

// Global instance
window.echoScanExcitement = new EchoScanExcitement();

// Usage example:
// window.echoScanExcitement.trigger(excitementData);
"""

def generate_css_animations() -> str:
    """Generate CSS animations for balloons and other effects"""
    
    return """
/* EchoScan Excitement Layer CSS Animations */

@keyframes float-up {
    0% {
        transform: translateY(0);
        opacity: 1;
    }
    100% {
        transform: translateY(-100vh);
        opacity: 0;
    }
}

@keyframes gentle-sway {
    0%, 100% {
        transform: translateX(0);
    }
    25% {
        transform: translateX(-5px);
    }
    75% {
        transform: translateX(5px);
    }
}

@keyframes sparkle {
    0%, 100% {
        opacity: 0;
        transform: scale(0);
    }
    50% {
        opacity: 1;
        transform: scale(1);
    }
}

@keyframes pulse-glow {
    0%, 100% {
        box-shadow: 0 0 5px rgba(255, 215, 0, 0.5);
    }
    50% {
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
    }
}

.echoscan-balloon {
    position: fixed;
    width: 40px;
    height: 50px;
    border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
    animation: float-up 3s ease-out forwards;
    z-index: 9998;
}

.echoscan-balloon::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    width: 1px;
    height: 30px;
    background-color: #333;
    transform: translateX(-50%);
}

.echoscan-sparkle {
    position: fixed;
    width: 4px;
    height: 4px;
    background-color: gold;
    border-radius: 50%;
    animation: sparkle 1s infinite;
    z-index: 9998;
}

.echoscan-message {
    position: fixed;
    top: 20%;
    left: 50%;
    transform: translateX(-50%);
    font-size: 2em;
    font-weight: bold;
    color: #333;
    text-align: center;
    z-index: 10000;
    pointer-events: none;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    animation: pulse-glow 2s infinite;
}

/* React/Streamlit specific classes */
.echoscan-excitement-container {
    position: relative;
    overflow: hidden;
}

.echoscan-verdict-display {
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    transition: all 0.3s ease;
}

.echoscan-verdict-authentic {
    background: linear-gradient(135deg, #90EE90, #98FB98);
    border: 2px solid #00FF00;
}

.echoscan-verdict-plausible {
    background: linear-gradient(135deg, #FFD700, #FFA500);
    border: 2px solid #FF8C00;
}

.echoscan-verdict-hallucination {
    background: linear-gradient(135deg, #FF6347, #FF4500);
    border: 2px solid #FF0000;
}

/* Streamlit specific styling */
.stApp .echoscan-excitement-container {
    margin: 10px 0;
}
"""

def generate_react_example() -> str:
    """Generate React component example"""
    
    return """
// React Component Example for EchoScan Excitement Layer

import React, { useEffect, useState } from 'react';

const EchoScanResults = ({ result }) => {
    const [excitementData, setExcitementData] = useState(null);
    
    useEffect(() => {
        if (result && window.echoScanExcitement) {
            // Generate excitement triggers based on result
            const triggers = generateExcitementTriggers(
                result.verdict, 
                result.confidence || 0.5, 
                result.echo_sense || 0.5
            );
            
            setExcitementData(triggers);
            
            // Trigger excitement after component renders
            setTimeout(() => {
                window.echoScanExcitement.trigger(triggers);
            }, 100);
        }
    }, [result]);
    
    const generateExcitementTriggers = (verdict, confidence, echoSense) => {
        // This would normally call your Python function
        // For demo purposes, implementing basic logic here
        
        const triggers = {
            excitement_enabled: true,
            verdict: verdict,
            confidence: confidence,
            echo_sense: echoSense,
            triggers: []
        };
        
        if (verdict === 'Authentic' && confidence > 0.8) {
            triggers.triggers.push({
                type: 'confetti',
                intensity: 'high',
                colors: ['#00FF00', '#00CC00', '#32CD32', '#90EE90'],
                duration: 3000,
                message: '🎉 Authentic Content Verified! 🎉'
            });
        } else if (verdict === 'Hallucination' && confidence > 0.7) {
            triggers.triggers.push({
                type: 'fireworks',
                pattern: 'warning',
                colors: ['red', 'orange', 'yellow'],
                count: 2,
                message: '⚠️ AI Generation Detected!'
            });
        }
        
        return triggers;
    };
    
    const getVerdictClass = (verdict) => {
        switch (verdict?.toLowerCase()) {
            case 'authentic': return 'echoscan-verdict-authentic';
            case 'plausible': return 'echoscan-verdict-plausible';
            case 'hallucination': return 'echoscan-verdict-hallucination';
            default: return '';
        }
    };
    
    if (!result) return <div>No results available</div>;
    
    return (
        <div className="echoscan-excitement-container">
            <div className={`echoscan-verdict-display ${getVerdictClass(result.verdict)}`}>
                <h2>EchoScan Analysis Result</h2>
                <p><strong>Verdict:</strong> {result.verdict}</p>
                <p><strong>Confidence:</strong> {(result.confidence * 100).toFixed(1)}%</p>
                <p><strong>EchoSense Score:</strong> {(result.echo_sense * 100).toFixed(1)}%</p>
                <p><strong>Delta S:</strong> {result.delta_s?.toFixed(5)}</p>
                <p><strong>Glyph ID:</strong> {result.glyph_id}</p>
            </div>
        </div>
    );
};

export default EchoScanResults;
"""

def generate_streamlit_example() -> str:
    """Generate Streamlit example code"""
    
    return """
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
"""

# Create files for the UI excitement layer
def create_excitement_files():
    """Create all excitement layer files"""
    
    # Create static directory for web assets
    os.makedirs('/home/runner/work/EchoScan/EchoScan/static', exist_ok=True)
    
    # Write JavaScript file
    with open('/home/runner/work/EchoScan/EchoScan/static/excitement.js', 'w') as f:
        f.write(generate_javascript_excitement())
    
    # Write CSS file  
    with open('/home/runner/work/EchoScan/EchoScan/static/excitement.css', 'w') as f:
        f.write(generate_css_animations())
    
    # Write React example
    with open('/home/runner/work/EchoScan/EchoScan/examples_react_excitement.jsx', 'w') as f:
        f.write(generate_react_example())
    
    # Write Streamlit example
    with open('/home/runner/work/EchoScan/EchoScan/examples_streamlit_excitement.py', 'w') as f:
        f.write(generate_streamlit_example())

if __name__ == '__main__':
    create_excitement_files()