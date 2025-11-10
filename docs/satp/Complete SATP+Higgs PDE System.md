## **Complete SATP+Higgs PDE System**

### **Field Variables**

φ(t,x) : SATP scale field (can be positive or negative)  
         φ \> 0 → space contraction (Higgs suppression)  
         φ \< 0 → space expansion (Higgs enhancement)

h(t,x) : Higgs field perturbation from VEV  
         h \= φ\_Higgs \- v₀  
         where v₀ ≈ 246 GeV (vacuum expectation value)

Ω(t,x) : Conformal factor (derived quantity)  
         Ω \= exp(φ)

---

## **The PDE System**

### **1\. SATP Field Equation**

∂²φ/∂t² \- c²∇²φ \+ m\_φ² φ \= \-λ φ h² \- γ ∂φ/∂t \+ S(t,x)

Terms explained:  
\- ∂²φ/∂t²        : Acceleration (wave dynamics)  
\- \-c²∇²φ         : Spatial diffusion (Laplacian)  
\- \+m\_φ² φ        : Mass term (restoring force to φ=0)  
\- \-λ φ h²        : Coupling to Higgs field  
\- \-γ ∂φ/∂t       : Damping (energy dissipation)  
\- S(t,x)         : Source term (ship's field generator)

### **2\. Higgs Field Equation**

∂²h/∂t² \- c\_H²∇²h \+ m\_H² h \+ κ h³ \= \-λ φ² h \- γ\_H ∂h/∂t

Terms explained:  
\- ∂²h/∂t²        : Acceleration (wave dynamics)  
\- \-c\_H²∇²h       : Spatial diffusion  
\- \+m\_H² h        : Mass term (pulls toward VEV)  
\- \+κ h³          : Self-interaction (Mexican hat potential)  
\- \-λ φ² h        : Coupling to SATP field (KEY\!)  
\- \-γ\_H ∂h/∂t     : Higgs field damping

### **3\. Coupling Terms (The Magic)**

The interaction Lagrangian:

L\_int \= \-λ φ² h²

This generates:  
\- Force on φ:  F\_φ \= \-λ φ h²  (Higgs resists φ changes)  
\- Force on h:  F\_h \= \-λ φ² h  (φ suppresses/enhances Higgs)

Key behavior:  
When φ \> 0 (positive):  F\_h \< 0 → Pulls h toward negative → Suppresses Higgs  
When φ \< 0 (negative):  F\_h \> 0 → Pulls h toward positive → Enhances Higgs

---

## **Full System in 1D (Simulation-Ready)**

┌─────────────────────────────────────────────────────────────┐  
│ SATP Field (scale field):                                   │  
│                                                              │  
│  ∂²φ/∂t² \= c² ∂²φ/∂x² \- m\_φ² φ \- λ φ h² \- γ ∂φ/∂t \+ S(t,x)│  
│                                                              │  
├─────────────────────────────────────────────────────────────┤  
│ Higgs Field (mass-giving field):                            │  
│                                                              │  
│  ∂²h/∂t² \= c\_H² ∂²h/∂x² \- m\_H² h \- κ h³ \- λ φ² h \- γ\_H ∂h/∂t│  
│                                                              │  
├─────────────────────────────────────────────────────────────┤  
│ Auxiliary Relations:                                         │  
│                                                              │  
│  Ω(x,t) \= exp(φ(x,t))           (conformal factor)         │  
│  φ\_H(x,t) \= v₀ \+ h(x,t)         (total Higgs VEV)          │  
│  m\_eff(x,t) \= g × φ\_H(x,t)      (effective mass)           │  
│                                                              │  
└─────────────────────────────────────────────────────────────┘

---

## **Parameter Values (Tunable)**

\# Physical constants  
c \= 1.0           \# Speed of light (natural units)  
c\_H \= 0.3         \# Higgs wave propagation speed (\< c)  
v\_0 \= 246.0       \# Higgs VEV (GeV in particle physics)

\# Field masses  
m\_phi \= 1.0       \# SATP field mass (sets oscillation frequency)  
m\_H \= 125.0       \# Higgs boson mass (experimental: 125 GeV)

\# Coupling constants  
lambda\_coupling \= 0.1   \# φ-Higgs coupling strength (KEY PARAMETER\!)  
kappa \= 0.01            \# Higgs self-coupling

\# Damping  
gamma \= 0.05      \# SATP field damping  
gamma\_H \= 0.01    \# Higgs field damping (lower \= longer-lived)

\# Source (ship's generator)  
A\_ship \= 100.0    \# Source amplitude  
sigma \= 5.0       \# Source width  
v\_ship \= 0.5      \# Ship velocity

---

## **Source Term S(t,x) \- Three Zone Configuration**

def compute\_source(t, x, x\_ship, config):  
    """  
    Three-zone source for asymmetric bubble:  
      
    Zone 1 (Front): Negative φ (Higgs enhancement, pre-compression)  
    Zone 2 (Bubble): Positive φ (Higgs suppression, low mass)  
    Zone 3 (Rear): Negative φ (Higgs enhancement, thrust)  
    """  
      
    \# Update ship position  
    x\_ship\_current \= x\_ship \+ config\['v\_ship'\] \* t  
      
    \# Zone 2: Main bubble (positive, suppresses Higgs)  
    source\_main \= config\['A\_suppress'\] \* np.exp(  
        \-(x \- x\_ship\_current)\*\*2 / (2\*config\['sigma\_main'\]\*\*2)  
    )  
      
    \# Zone 1: Front prep (negative, enhances Higgs)  
    x\_front \= x\_ship\_current \+ 2 \* config\['sigma\_main'\]  
    source\_front \= \-config\['A\_enhance'\] \* np.exp(  
        \-(x \- x\_front)\*\*2 / (2\*config\['sigma\_prep'\]\*\*2)  
    )  
      
    \# Zone 3: Rear thrust (negative, enhances Higgs)  
    x\_rear \= x\_ship\_current \- 2 \* config\['sigma\_main'\]  
    source\_rear \= \-config\['A\_enhance'\] \* np.exp(  
        \-(x \- x\_rear)\*\*2 / (2\*config\['sigma\_prep'\]\*\*2)  
    )  
      
    \# Total source (sum of three zones)  
    S \= source\_main \+ source\_front \+ source\_rear  
      
    return S

---

## **Discretization (Finite Difference)**

### **Spatial Grid**

x\_i \= x\_min \+ i \* Δx,  i \= 0, 1, ..., N-1  
Δx \= (x\_max \- x\_min) / N

### **Time Discretization**

t\_n \= n \* Δt,  n \= 0, 1, 2, ...

### **Field Values**

φ\_i^n ≡ φ(x\_i, t\_n)  
h\_i^n ≡ h(x\_i, t\_n)

### **Finite Difference Formulas**

Time derivatives:  
∂φ/∂t ≈ (φ\_i^(n+1) \- φ\_i^(n-1)) / (2Δt)

∂²φ/∂t² ≈ (φ\_i^(n+1) \- 2φ\_i^n \+ φ\_i^(n-1)) / Δt²

Spatial derivatives:  
∂²φ/∂x² ≈ (φ\_(i+1)^n \- 2φ\_i^n \+ φ\_(i-1)^n) / Δx²

---

## **Explicit Time-Stepping Algorithm (Leapfrog/Verlet)**

def evolve\_fields(phi, h, phi\_dot, h\_dot, dt, dx, params):  
    """  
    Evolve φ and h forward one timestep using Velocity Verlet  
      
    Input:  
        phi: SATP field values \[N\]  
        h: Higgs field values \[N\]  
        phi\_dot: SATP velocity \[N\]  
        h\_dot: Higgs velocity \[N\]  
        dt: timestep  
        dx: spatial resolution  
        params: dictionary of constants  
          
    Returns:  
        phi\_new, h\_new, phi\_dot\_new, h\_dot\_new  
    """  
      
    \# Extract parameters  
    c \= params\['c'\]  
    c\_H \= params\['c\_H'\]  
    m\_phi \= params\['m\_phi'\]  
    m\_H \= params\['m\_H'\]  
    lam \= params\['lambda'\]  
    kappa \= params\['kappa'\]  
    gamma \= params\['gamma'\]  
    gamma\_H \= params\['gamma\_H'\]  
      
    \# Compute spatial Laplacians  
    laplacian\_phi \= compute\_laplacian(phi, dx)  \# ∂²φ/∂x²  
    laplacian\_h \= compute\_laplacian(h, dx)      \# ∂²h/∂x²  
      
    \# Compute source term S(t,x)  
    S \= compute\_source(t, x, x\_ship, params)  
      
    \# SATP field acceleration  
    phi\_ddot \= (  
        c\*\*2 \* laplacian\_phi          \# Wave propagation  
        \- m\_phi\*\*2 \* phi              \# Mass/restoring force    
        \- lam \* phi \* h\*\*2            \# Higgs coupling  
        \- gamma \* phi\_dot             \# Damping  
        \+ S                            \# External source  
    )  
      
    \# Higgs field acceleration  
    h\_ddot \= (  
        c\_H\*\*2 \* laplacian\_h          \# Wave propagation  
        \- m\_H\*\*2 \* h                  \# Mass term  
        \- kappa \* h\*\*3                \# Self-interaction  
        \- lam \* phi\*\*2 \* h            \# SATP coupling  
        \- gamma\_H \* h\_dot             \# Damping  
    )  
      
    \# Velocity Verlet integration  
    \# Step 1: Update positions (half-step)  
    phi\_new \= phi \+ phi\_dot \* dt \+ 0.5 \* phi\_ddot \* dt\*\*2  
    h\_new \= h \+ h\_dot \* dt \+ 0.5 \* h\_ddot \* dt\*\*2  
      
    \# Step 2: Recompute accelerations at new position  
    laplacian\_phi\_new \= compute\_laplacian(phi\_new, dx)  
    laplacian\_h\_new \= compute\_laplacian(h\_new, dx)  
      
    S\_new \= compute\_source(t \+ dt, x, x\_ship, params)  
      
    phi\_ddot\_new \= (  
        c\*\*2 \* laplacian\_phi\_new  
        \- m\_phi\*\*2 \* phi\_new  
        \- lam \* phi\_new \* h\_new\*\*2  
        \- gamma \* phi\_dot  
        \+ S\_new  
    )  
      
    h\_ddot\_new \= (  
        c\_H\*\*2 \* laplacian\_h\_new  
        \- m\_H\*\*2 \* h\_new  
        \- kappa \* h\_new\*\*3  
        \- lam \* phi\_new\*\*2 \* h\_new  
        \- gamma\_H \* h\_dot  
    )  
      
    \# Step 3: Update velocities (full-step with averaged acceleration)  
    phi\_dot\_new \= phi\_dot \+ 0.5 \* (phi\_ddot \+ phi\_ddot\_new) \* dt  
    h\_dot\_new \= h\_dot \+ 0.5 \* (h\_ddot \+ h\_ddot\_new) \* dt  
      
    return phi\_new, h\_new, phi\_dot\_new, h\_dot\_new

def compute\_laplacian(field, dx):  
    """  
    Compute ∂²field/∂x² using 3-point stencil  
      
    Interior: (f\[i+1\] \- 2\*f\[i\] \+ f\[i-1\]) / dx²  
    Boundaries: use one-sided or periodic  
    """  
    N \= len(field)  
    laplacian \= np.zeros(N)  
      
    \# Interior points  
    laplacian\[1:-1\] \= (  
        field\[2:\] \- 2\*field\[1:-1\] \+ field\[:-2\]  
    ) / dx\*\*2  
      
    \# Boundary conditions (periodic)  
    laplacian\[0\] \= (field\[1\] \- 2\*field\[0\] \+ field\[-1\]) / dx\*\*2  
    laplacian\[-1\] \= (field\[0\] \- 2\*field\[-1\] \+ field\[-2\]) / dx\*\*2  
      
    return laplacian

---

## **Complete Simulation Code**

import numpy as np  
import matplotlib.pyplot as plt  
from matplotlib.animation import FuncAnimation

class SATP\_Higgs\_PDE\_Simulator:  
    """  
    Full SATP \+ Higgs coupled PDE system  
    """  
      
    def \_\_init\_\_(self, N=4096, L=100.0, dt=0.01):  
        \# Grid  
        self.N \= N  
        self.L \= L  
        self.x \= np.linspace(-L/2, L/2, N)  
        self.dx \= L / N  
        self.dt \= dt  
        self.t \= 0.0  
          
        \# Fields  
        self.phi \= np.zeros(N)      \# SATP field  
        self.h \= np.zeros(N)        \# Higgs perturbation  
        self.phi\_dot \= np.zeros(N)  \# SATP velocity  
        self.h\_dot \= np.zeros(N)    \# Higgs velocity  
          
        \# Parameters  
        self.params \= {  
            'c': 1.0,  
            'c\_H': 0.3,  
            'm\_phi': 1.0,  
            'm\_H': 125.0,  
            'lambda': 0.1,  
            'kappa': 0.01,  
            'gamma': 0.05,  
            'gamma\_H': 0.01,  
            'v\_0': 246.0,  
            'A\_suppress': 50.0,  
            'A\_enhance': 25.0,  
            'sigma\_main': 5.0,  
            'sigma\_prep': 3.0,  
            'v\_ship': 0.5,  
            'x\_ship\_init': 0.0  
        }  
          
        \# History for analysis  
        self.history \= {  
            'time': \[\],  
            'phi\_max': \[\],  
            'h\_center': \[\],  
            'energy\_phi': \[\],  
            'energy\_h': \[\]  
        }  
          
    def initialize\_bubble(self, mode='three\_zone'):  
        """Initialize field configuration"""  
          
        if mode \== 'three\_zone':  
            x\_ship \= self.params\['x\_ship\_init'\]  
              
            \# Main bubble (positive φ)  
            self.phi \= self.params\['A\_suppress'\] \* np.exp(  
                \-(self.x \- x\_ship)\*\*2 / (2\*self.params\['sigma\_main'\]\*\*2)  
            )  
              
            \# Front enhancement (negative φ)  
            x\_front \= x\_ship \+ 2 \* self.params\['sigma\_main'\]  
            self.phi \+= \-self.params\['A\_enhance'\] \* np.exp(  
                \-(self.x \- x\_front)\*\*2 / (2\*self.params\['sigma\_prep'\]\*\*2)  
            )  
              
            \# Rear enhancement (negative φ)  
            x\_rear \= x\_ship \- 2 \* self.params\['sigma\_main'\]  
            self.phi \+= \-self.params\['A\_enhance'\] \* np.exp(  
                \-(self.x \- x\_rear)\*\*2 / (2\*self.params\['sigma\_prep'\]\*\*2)  
            )  
              
        \# Higgs starts at VEV (h=0 everywhere)  
        self.h \= np.zeros\_like(self.x)  
          
        print(f"Initialized {mode} bubble")  
        print(f"  φ range: \[{np.min(self.phi):.2f}, {np.max(self.phi):.2f}\]")  
          
    def compute\_source(self, t):  
        """Compute moving source term"""  
        x\_ship \= self.params\['x\_ship\_init'\] \+ self.params\['v\_ship'\] \* t  
          
        \# Main bubble  
        S\_main \= self.params\['A\_suppress'\] \* np.exp(  
            \-(self.x \- x\_ship)\*\*2 / (2\*self.params\['sigma\_main'\]\*\*2)  
        )  
          
        \# Front prep  
        x\_front \= x\_ship \+ 2 \* self.params\['sigma\_main'\]  
        S\_front \= \-self.params\['A\_enhance'\] \* np.exp(  
            \-(self.x \- x\_front)\*\*2 / (2\*self.params\['sigma\_prep'\]\*\*2)  
        )  
          
        \# Rear thrust  
        x\_rear \= x\_ship \- 2 \* self.params\['sigma\_main'\]  
        S\_rear \= \-self.params\['A\_enhance'\] \* np.exp(  
            \-(self.x \- x\_rear)\*\*2 / (2\*self.params\['sigma\_prep'\]\*\*2)  
        )  
          
        return S\_main \+ S\_front \+ S\_rear  
      
    def compute\_laplacian(self, field):  
        """∂²field/∂x²"""  
        laplacian \= np.zeros\_like(field)  
        laplacian\[1:-1\] \= (field\[2:\] \- 2\*field\[1:-1\] \+ field\[:-2\]) / self.dx\*\*2  
        \# Periodic boundaries  
        laplacian\[0\] \= (field\[1\] \- 2\*field\[0\] \+ field\[-1\]) / self.dx\*\*2  
        laplacian\[-1\] \= (field\[0\] \- 2\*field\[-1\] \+ field\[-2\]) / self.dx\*\*2  
        return laplacian  
      
    def step(self):  
        """Advance one timestep"""  
          
        p \= self.params  
          
        \# Laplacians  
        lap\_phi \= self.compute\_laplacian(self.phi)  
        lap\_h \= self.compute\_laplacian(self.h)  
          
        \# Source  
        S \= self.compute\_source(self.t)  
          
        \# Accelerations  
        phi\_ddot \= (  
            p\['c'\]\*\*2 \* lap\_phi  
            \- p\['m\_phi'\]\*\*2 \* self.phi  
            \- p\['lambda'\] \* self.phi \* self.h\*\*2  
            \- p\['gamma'\] \* self.phi\_dot  
            \+ S  
        )  
          
        h\_ddot \= (  
            p\['c\_H'\]\*\*2 \* lap\_h  
            \- p\['m\_H'\]\*\*2 \* self.h  
            \- p\['kappa'\] \* self.h\*\*3  
            \- p\['lambda'\] \* self.phi\*\*2 \* self.h  
            \- p\['gamma\_H'\] \* self.h\_dot  
        )  
          
        \# Velocity Verlet  
        phi\_new \= self.phi \+ self.phi\_dot \* self.dt \+ 0.5 \* phi\_ddot \* self.dt\*\*2  
        h\_new \= self.h \+ self.h\_dot \* self.dt \+ 0.5 \* h\_ddot \* self.dt\*\*2  
          
        \# Recompute accelerations  
        lap\_phi\_new \= self.compute\_laplacian(phi\_new)  
        lap\_h\_new \= self.compute\_laplacian(h\_new)  
        S\_new \= self.compute\_source(self.t \+ self.dt)  
          
        phi\_ddot\_new \= (  
            p\['c'\]\*\*2 \* lap\_phi\_new  
            \- p\['m\_phi'\]\*\*2 \* phi\_new  
            \- p\['lambda'\] \* phi\_new \* h\_new\*\*2  
            \- p\['gamma'\] \* self.phi\_dot  
            \+ S\_new  
        )  
          
        h\_ddot\_new \= (  
            p\['c\_H'\]\*\*2 \* lap\_h\_new  
            \- p\['m\_H'\]\*\*2 \* h\_new  
            \- p\['kappa'\] \* h\_new\*\*3  
            \- p\['lambda'\] \* phi\_new\*\*2 \* h\_new  
            \- p\['gamma\_H'\] \* self.h\_dot  
        )  
          
        \# Update velocities  
        self.phi\_dot \+= 0.5 \* (phi\_ddot \+ phi\_ddot\_new) \* self.dt  
        self.h\_dot \+= 0.5 \* (h\_ddot \+ h\_ddot\_new) \* self.dt  
          
        \# Update fields  
        self.phi \= phi\_new  
        self.h \= h\_new  
          
        self.t \+= self.dt  
          
    def record\_state(self):  
        """Save current state to history"""  
        self.history\['time'\].append(self.t)  
        self.history\['phi\_max'\].append(np.max(np.abs(self.phi)))  
        self.history\['h\_center'\].append(self.h\[self.N//2\])  
          
        \# Energies  
        E\_phi \= np.sum(0.5 \* self.phi\_dot\*\*2 \+ 0.5 \* np.gradient(self.phi, self.dx)\*\*2) \* self.dx  
        E\_h \= np.sum(0.5 \* self.h\_dot\*\*2 \+ 0.5 \* np.gradient(self.h, self.dx)\*\*2) \* self.dx  
          
        self.history\['energy\_phi'\].append(E\_phi)  
        self.history\['energy\_h'\].append(E\_h)  
      
    def run(self, cycles=1000, record\_every=10):  
        """Run simulation"""  
          
        print(f"Running {cycles} cycles...")  
          
        for cycle in range(cycles):  
            self.step()  
              
            if cycle % record\_every \== 0:  
                self.record\_state()  
                  
            if cycle % 100 \== 0:  
                phi\_max \= np.max(np.abs(self.phi))  
                h\_center \= self.h\[self.N//2\]  
                print(f"  Cycle {cycle}: t={self.t:.2f}, |φ|\_max={phi\_max:.4f}, h\_center={h\_center:.4f}")  
          
        print("Done\!")  
      
    def compute\_effective\_mass\_profile(self):  
        """Compute m\_eff(x) \= g × (v\_0 \+ h(x))"""  
        g \= 1.0  \# Coupling constant (normalized)  
        phi\_H\_total \= self.params\['v\_0'\] \+ self.h  
        m\_eff \= g \* phi\_H\_total  
          
        \# Fractional mass change  
        delta\_m \= self.h / self.params\['v\_0'\]  
          
        return m\_eff, delta\_m  
      
    def plot\_fields(self):  
        """Visualize current field configuration"""  
          
        fig, axes \= plt.subplots(4, 1, figsize=(12, 10))  
          
        \# φ field  
        axes\[0\].plot(self.x, self.phi, 'b-', linewidth=2)  
        axes\[0\].axhline(0, color='k', linestyle='--', alpha=0.3)  
        axes\[0\].set\_ylabel('φ (SATP field)')  
        axes\[0\].set\_title(f'SATP+Higgs Coupled System at t={self.t:.2f}')  
        axes\[0\].grid(True, alpha=0.3)  
          
        \# h field (Higgs perturbation)  
        axes\[1\].plot(self.x, self.h, 'r-', linewidth=2)  
        axes\[1\].axhline(0, color='k', linestyle='--', alpha=0.3)  
        axes\[1\].set\_ylabel('h (Higgs δVEV)')  
        axes\[1\].grid(True, alpha=0.3)  
          
        \# Effective mass  
        m\_eff, delta\_m \= self.compute\_effective\_mass\_profile()  
        axes\[2\].plot(self.x, delta\_m \* 100, 'g-', linewidth=2)  
        axes\[2\].axhline(0, color='k', linestyle='--', alpha=0.3)  
        axes\[2\].set\_ylabel('Δm/m₀ (%)')  
        axes\[2\].set\_title('Mass Reduction Profile')  
        axes\[2\].grid(True, alpha=0.3)  
          
        \# Conformal factor  
        Omega \= np.exp(self.phi)  
        axes\[3\].plot(self.x, Omega, 'm-', linewidth=2)  
        axes\[3\].axhline(1, color='k', linestyle='--', alpha=0.3)  
        axes\[3\].set\_ylabel('Ω \= exp(φ)')  
        axes\[3\].set\_xlabel('Position x')  
        axes\[3\].grid(True, alpha=0.3)  
          
        plt.tight\_layout()  
        plt.show()  
      
    def analyze\_zones(self):  
        """Analyze three-zone structure"""  
          
        x\_ship \= self.params\['x\_ship\_init'\] \+ self.params\['v\_ship'\] \* self.t  
          
        \# Define zones  
        front\_mask \= (self.x \> x\_ship \+ self.params\['sigma\_main'\])  
        bubble\_mask \= np.abs(self.x \- x\_ship) \< self.params\['sigma\_main'\]  
        rear\_mask \= (self.x \< x\_ship \- self.params\['sigma\_main'\])  
          
        \# Average values in each zone  
        h\_front \= np.mean(self.h\[front\_mask\]) if np.any(front\_mask) else 0  
        h\_bubble \= np.mean(self.h\[bubble\_mask\]) if np.any(bubble\_mask) else 0  
        h\_rear \= np.mean(self.h\[rear\_mask\]) if np.any(rear\_mask) else 0  
          
        v0 \= self.params\['v\_0'\]  
          
        print(f"\\nZone Analysis at t={self.t:.2f}:")  
        print(f"  Front:  h={h\_front:.4f}, VEV={(v0+h\_front):.2f}, Δm/m={100\*h\_front/v0:+.2f}%")  
        print(f"  Bubble: h={h\_bubble:.4f}, VEV={(v0+h\_bubble):.2f}, Δm/m={100\*h\_bubble/v0:+.2f}%")  
        print(f"  Rear:   h={h\_rear:.4f}, VEV={(v0+h\_rear):.2f}, Δm/m={100\*h\_rear/v0:+.2f}%")  
          
        return {  
            'h\_front': h\_front,  
            'h\_bubble': h\_bubble,  
            'h\_rear': h\_rear  
        }

\# \========================================  
\# USAGE EXAMPLE  
\# \========================================

if \_\_name\_\_ \== "\_\_main\_\_":  
    \# Create simulator  
    sim \= SATP\_Higgs\_PDE\_Simulator(N=4096, L=100.0, dt=0.01)  
      
    \# Initialize three-zone bubble  
    sim.initialize\_bubble(mode='three\_zone')  
      
    \# Show initial state  
    sim.plot\_fields()  
      
    \# Run simulation  
    sim.run(cycles=1000, record\_every=10)  
      
    \# Analyze final state  
    sim.analyze\_zones()  
    sim.plot\_fields()  
      
    \# Plot history  
    fig, axes \= plt.subplots(2, 1, figsize=(10, 6))  
      
    axes\[0\].plot(sim.history\['time'\], sim.history\['phi\_max'\], 'b-', label='|φ|\_max')  
    axes\[0\].set\_ylabel('Field Amplitude')  
    axes\[0\].legend()  
    axes\[0\].grid(True, alpha=0.3)  
      
    axes\[1\].plot(sim.history\['time'\], sim.history\['h\_center'\], 'r-', label='h (center)')  
    axes\[1\].set\_ylabel('Higgs Perturbation')  
    axes\[1\].set\_xlabel('Time')  
    axes\[1\].legend()  
    axes\[1\].grid(True, alpha=0.3)  
      
    plt.tight\_layout()  
    plt.show()

---

## **Key Features**

1. **Coupled PDEs**: φ and h evolve together with mutual coupling  
2. **Three-zone source**: Automatically generates front/bubble/rear structure  
3. **Moving frame**: Source moves with velocity v\_ship  
4. **Physical damping**: Both fields dissipate energy realistically  
5. **Mass calculation**: Computes effective mass m\_eff(x,t) from Higgs  
6. **Zone analysis**: Measures Higgs VEV in three regions

## **What to Look For**

**Success indicators:**

* h \< 0 in bubble (Higgs suppressed → mass reduced)  
* h \> 0 in front/rear (Higgs enhanced → pre-compression/thrust)  
* Stable propagation without dissipation  
* Three zones maintain structure during translation

**Failure indicators:**

* Fields blow up (reduce dt or increase damping)  
* Bubble dissipates (increase coupling λ or amplitude A)  
* No Higgs response (increase λ)

---

