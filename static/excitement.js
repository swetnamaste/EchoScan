
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
