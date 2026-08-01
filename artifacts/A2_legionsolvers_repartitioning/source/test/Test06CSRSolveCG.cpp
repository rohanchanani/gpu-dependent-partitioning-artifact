#include <cassert>
#include <iostream>

#include <legion.h>
#include <realm/cmdline.h>

#include "CGSolver.hpp"
#include "CSRMatrix.hpp"
#include "ExampleSystems.hpp"
#include "Initialize.hpp"
#include "LegionUtilities.hpp"
#include "LibraryOptions.hpp"
#include "PartitionedVector.hpp"
#include "SquarePlanner.hpp"


using ENTRY_T = double;
constexpr int VECTOR_DIM = 1;
constexpr int VECTOR_COLOR_DIM = 1;
using VECTOR_COORD_T = Legion::coord_t;
using VECTOR_COLOR_COORD_T = Legion::coord_t;
using VectorRect = Legion::Rect<VECTOR_DIM, VECTOR_COORD_T>;
using VectorColorRect = Legion::Rect<VECTOR_COLOR_DIM, VECTOR_COLOR_COORD_T>;

enum TaskIDs : Legion::TaskID { TOP_LEVEL_TASK_ID };


void top_level_task(
    const Legion::Task *,
    const std::vector<Legion::PhysicalRegion> &,
    Legion::Context ctx,
    Legion::Runtime *rt
) {
    VECTOR_COORD_T grid_size = 100;
    VECTOR_COLOR_COORD_T num_vector_pieces = 4;
    std::size_t num_iterations = 10;
    std::size_t repartition_interval = 0;
    bool no_print_results = false;

    const Legion::InputArgs &args = Legion::Runtime::get_input_args();
    [[maybe_unused]] bool ok =
        Realm::CommandLineParser()
            .add_option_int("-n", grid_size)
            .add_option_int("-vp", num_vector_pieces)
            .add_option_int("-it", num_iterations)
            .add_option_int("-rp", repartition_interval)
            .add_option_bool("-np", no_print_results)
            .parse_command_line(args.argc, (const char **) args.argv);
    assert(ok);

    const auto vector_color_space =
        rt->create_index_space(ctx, VectorColorRect{0, num_vector_pieces - 1});

    LegionSolvers::CSRMatrix<ENTRY_T> csr_matrix =
        LegionSolvers::csr_negative_laplacian_1d<ENTRY_T>(
            ctx, rt, grid_size, vector_color_space
        );

    const auto vector_index_space =
        csr_matrix.get_auxiliary_regions()[0].get_index_space();

    const auto disjoint_vector_partition =
        rt->create_equal_partition(ctx, vector_index_space, vector_color_space);

    LegionSolvers::PartitionedVector<ENTRY_T> rhs(
        ctx, rt, "rhs", disjoint_vector_partition
    );
    rhs.constant_fill(1.0);

    LegionSolvers::PartitionedVector<ENTRY_T> sol(
        ctx, rt, "sol", disjoint_vector_partition
    );
    sol.zero_fill();

    LegionSolvers::SquarePlanner<ENTRY_T> planner{ctx, rt};
    planner.add_sol_vector(sol);
    planner.add_rhs_vector(rhs);
    planner.add_row_partitioned_matrix(csr_matrix, 0, 0);

    LegionSolvers::CGSolver<ENTRY_T> solver{planner};

    rt->issue_execution_fence(ctx);
    rt->issue_mapping_fence(ctx);

    const Legion::Future begin_time_future =
        rt->get_current_time_in_nanoseconds(ctx);

    rt->issue_execution_fence(ctx);
    rt->issue_mapping_fence(ctx);

    for (std::size_t i = 0; i < num_iterations; ++i) {
        solver.step();
        if (repartition_interval > 0 &&
            ((i + 1) % repartition_interval) == 0 &&
            (i + 1) < num_iterations) {
            const Legion::IndexPartition next_partition =
                rt->create_equal_partition(
                    ctx, vector_index_space, vector_color_space
                );
            planner.repartition(0, next_partition);
#ifndef LEGION_SOLVERS_DISABLE_CLEANUP
            rt->destroy_index_partition(ctx, next_partition);
#endif // LEGION_SOLVERS_DISABLE_CLEANUP
        }
    }

    rt->issue_execution_fence(ctx);
    rt->issue_mapping_fence(ctx);

    const Legion::Future end_time_future =
        rt->get_current_time_in_nanoseconds(ctx);

    rt->issue_execution_fence(ctx);
    rt->issue_mapping_fence(ctx);

    const long long begin_time = begin_time_future.get_result<long long>();
    const long long end_time = end_time_future.get_result<long long>();
    const double elapsed_seconds =
        static_cast<double>(end_time - begin_time) / 1.0e9;
    const double iterations_per_second =
        elapsed_seconds > 0.0 ?
            static_cast<double>(num_iterations) / elapsed_seconds :
            0.0;
    const double mpoints_per_second =
        iterations_per_second * static_cast<double>(grid_size) / 1.0e6;
    const double gnnz_spmv_per_second =
        iterations_per_second *
        static_cast<double>(3 * grid_size - 2) / 1.0e9;

    if (rt->get_shard_id(ctx, true) == 0) {
        std::cout << "THROUGHPUT"
                  << " n=" << grid_size
                  << " it=" << num_iterations
                  << " rp=" << repartition_interval
                  << " seconds=" << elapsed_seconds
                  << " iter_per_sec=" << iterations_per_second
                  << " mpoints_per_sec=" << mpoints_per_second
                  << " gnnz_spmv_per_sec=" << gnnz_spmv_per_second
                  << std::endl;
    }

    if (!no_print_results) {
        Legion::Future dummy = Legion::Future::from_value<int>(rt, 0);
        for (std::size_t i = 0; i <= num_iterations; ++i) {
            dummy = solver.residual_norm_squared[i].print(dummy);
        }
    }

#ifndef LEGION_SOLVERS_DISABLE_CLEANUP
    rt->destroy_index_partition(ctx, disjoint_vector_partition);
    rt->destroy_index_space(ctx, vector_color_space);
#endif // LEGION_SOLVERS_DISABLE_CLEANUP
}


int main(int argc, char **argv) {
    using LegionSolvers::TaskFlags;
    LegionSolvers::initialize(false, false);
    LegionSolvers::preregister_task<top_level_task>(
        TOP_LEVEL_TASK_ID,
        "top_level",
        Legion::Processor::LOC_PROC,
        TaskFlags::INNER | TaskFlags::REPLICABLE
    );
    Legion::Runtime::set_top_level_task_id(TOP_LEVEL_TASK_ID);
    Legion::Runtime::set_top_level_task_mapper_id(
        LegionSolvers::LEGION_SOLVERS_MAPPER_ID
    );
    return Legion::Runtime::start(argc, argv);
}
