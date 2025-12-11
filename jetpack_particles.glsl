// Origin of the particles (player position)
uniform vec2 pos;
// Time offset for continuous particle generation
uniform float timeOffset;

// Constants
// Number of particles
const float PARTICLE_COUNT = 50.0;
// Max distance particles can travel downward (normalized)
const float MAX_PARTICLE_DISTANCE = 0.15;
// Size of each particle (normalized)
const float PARTICLE_SIZE = 0.004;
// Time for each particle to fall (in seconds)
const float PARTICLE_LIFETIME = 0.3;
// Spread angle for particles (radians)
const float SPREAD_ANGLE = 0.4;
const float TWOPI = 6.2832;

// Random function for particle direction
vec2 Hash12_Polar(float t) {
  float angle = fract(sin(t * 674.3) * 453.2) * TWOPI;
  float distance = fract(sin((t + angle) * 724.3) * 341.2);
  return vec2(sin(angle), cos(angle)) * distance;
}

void mainImage( out vec4 fragColor, in vec2 fragCoord ) {
  
  // Normalized pixel coordinates
  // Origin of the particles (player position)
  vec2 npos = (pos - .5 * iResolution.xy) / iResolution.y;
  // Position of current pixel we are drawing
  vec2 uv = (fragCoord - .5 * iResolution.xy) / iResolution.y;

  // Re-center based on input coordinates
  uv -= npos;

  // Default alpha is transparent
  float alpha = 0.0;

  // Loop for each particle
  for (float i = 0.0; i < PARTICLE_COUNT; i++) {
    float seed = i + 1.0;
    
    // Generate random direction with downward bias
    vec2 randomDir = Hash12_Polar(seed);
    // Create downward direction with some spread
    float angle = randomDir.x * SPREAD_ANGLE - SPREAD_ANGLE * 0.5;
    vec2 dir = vec2(sin(angle), -abs(cos(angle))); // Downward bias
    
    // Calculate particle spawn time offset
    float spawnTime = fract(i / PARTICLE_COUNT) * PARTICLE_LIFETIME;
    float particleAge = mod(iTime - timeOffset + spawnTime, PARTICLE_LIFETIME);
    
    // Only render particles that are within their lifetime
    if (particleAge < PARTICLE_LIFETIME) {
      // Calculate particle position based on age
      float timeFract = particleAge / PARTICLE_LIFETIME;
      // Particles fall downward and spread slightly
      vec2 particlePosition = dir * MAX_PARTICLE_DISTANCE * timeFract;
      
      // Add some randomness to the position
      particlePosition += randomDir * 0.02 * (1.0 - timeFract);
      
      // Distance of this pixel from that particle
      float d = length(uv - particlePosition);
      
      // If we are within the particle size, add to alpha
      if (d < PARTICLE_SIZE) {
        // Fade out as particle ages
        float fade = 1.0 - timeFract;
        alpha = max(alpha, fade);
      }
    }
  }
  
  // Output orange/yellow particles (matching fuel bar color)
  // RGB: (255, 98, 0) normalized to 0-1 range
  vec3 particleColor = vec3(1.0, 0.384, 0.0);
  fragColor = vec4(particleColor, alpha);
}

