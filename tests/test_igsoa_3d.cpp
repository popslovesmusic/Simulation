#include "../src/cpp/igsoa_complex_engine_3d.h"
#include "../src/cpp/igsoa_state_init_3d.h"
#include <cmath>
#include <iostream>

int main() {
    using namespace dase::igsoa;

    const size_t N_x = 16;
    const size_t N_y = 16;
    const size_t N_z = 16;

    IGSOAComplexConfig config;
    config.num_nodes = N_x * N_y * N_z;
    config.R_c_default = 3.0;
    config.kappa = 1.0;
    config.gamma = 0.1;
    config.dt = 0.01;
    config.normalize_psi = false;

    IGSOAComplexEngine3D engine(config, N_x, N_y, N_z);

    IGSOAStateInit3D::initSphericalGaussian(
        engine,
        /*amplitude=*/1.0,
        static_cast<double>(N_x) / 2.0,
        static_cast<double>(N_y) / 2.0,
        static_cast<double>(N_z) / 2.0,
        /*sigma=*/3.0,
        /*baseline_phi=*/0.0,
        /*mode=*/"overwrite",
        /*beta=*/1.0
    );

    double x0 = 0.0;
    double y0 = 0.0;
    double z0 = 0.0;
    IGSOAStateInit3D::computeCenterOfMass(engine, x0, y0, z0);

    engine.runMission(6);

    double x1 = 0.0;
    double y1 = 0.0;
    double z1 = 0.0;
    IGSOAStateInit3D::computeCenterOfMass(engine, x1, y1, z1);

    const double drift = std::sqrt(
        (x1 - x0) * (x1 - x0) +
        (y1 - y0) * (y1 - y0) +
        (z1 - z0) * (z1 - z0)
    );

    if (drift > 0.75) {
        std::cerr << "3D center-of-mass drift too large: " << drift << std::endl;
        return 1;
    }

    bool phi_dot_nonzero = false;
    for (const auto& node : engine.getNodes()) {
        if (std::abs(node.phi_dot) > 1e-9) {
            phi_dot_nonzero = true;
            break;
        }
    }

    if (!phi_dot_nonzero) {
        std::cerr << "Expected phi_dot to update during evolution" << std::endl;
        return 1;
    }

    std::cout << "Initial center: (" << x0 << ", " << y0 << ", " << z0 << ")\n";
    std::cout << "Final center: (" << x1 << ", " << y1 << ", " << z1 << ")\n";
    std::cout << "Drift: " << drift << std::endl;
    return 0;
}
