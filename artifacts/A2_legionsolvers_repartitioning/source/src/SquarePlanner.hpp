#ifndef LEGION_SOLVERS_SQUARE_PLANNER_HPP_INCLUDED
#define LEGION_SOLVERS_SQUARE_PLANNER_HPP_INCLUDED

#include <cassert> // for assert
#include <memory>  // for std::unique_ptr
#include <string>  // for std::to_string
#include <tuple>   // for std::tuple
#include <vector>  // for std::vector

#include <legion.h> // for Legion::*

#include "AbstractMatrix.hpp"
#include "LegionUtilities.hpp"
#include "PartitionedVector.hpp"

namespace LegionSolvers {


template <typename ENTRY_T>
class SquarePlanner {

    const Legion::Context ctx;
    Legion::Runtime *const rt;

    std::vector<Legion::IndexSpace> canonical_index_spaces;
    std::vector<Legion::IndexPartition> canonical_index_partitions;

    Legion::FieldSpace workspace_fields;
    std::vector<Legion::LogicalRegion> workspace_regions;
    std::vector<Legion::LogicalPartition> workspace_partitions;

    std::vector<std::unique_ptr<PartitionedVector<ENTRY_T>>> sol_vectors;
    std::vector<std::unique_ptr<PartitionedVector<ENTRY_T>>> rhs_vectors;
    std::vector<std::vector<std::unique_ptr<PartitionedVector<ENTRY_T>>>>
        workspace_vectors;

    struct RowPartitionedMatrix {
        const AbstractMatrix<ENTRY_T> *matrix;
        std::size_t domain_index;
        std::size_t range_index;
    };

    struct RowPartitionedMatrixArtifacts {
        Legion::IndexPartition kernel_index_partition;
        Legion::LogicalPartition kernel_logical_partition;
        Legion::IndexPartition ghost_partition;
    };

    std::vector<RowPartitionedMatrix> row_partitioned_matrices;
    std::vector<RowPartitionedMatrixArtifacts> row_partitioned_matrix_artifacts;

    std::vector<std::tuple<
        const AbstractMatrix<ENTRY_T> *,
        std::size_t,       // domain index
        std::size_t,       // range index
        Legion::IndexSpace // sparse index launch domain
        >>
        tile_partitioned_matrices;

public:

    explicit SquarePlanner(Legion::Context ctx, Legion::Runtime *rt)
        : ctx(ctx)
        , rt(rt)
        , canonical_index_spaces()
        , canonical_index_partitions()
        , workspace_fields(Legion::FieldSpace::NO_SPACE)
        , workspace_regions()
        , workspace_partitions()
        , sol_vectors()
        , rhs_vectors()
        , workspace_vectors()
        , row_partitioned_matrices()
        , row_partitioned_matrix_artifacts()
        , tile_partitioned_matrices() {}

    ~SquarePlanner() {
#ifndef LEGION_SOLVERS_DISABLE_CLEANUP
        destroy_row_partition_artifacts();
        for (const auto &region : workspace_regions) {
            rt->destroy_logical_region(ctx, region);
        }
        if (workspace_fields != Legion::FieldSpace::NO_SPACE) {
            rt->destroy_field_space(ctx, workspace_fields);
        }
        for (const auto &index_partition : canonical_index_partitions) {
            rt->destroy_index_partition(ctx, index_partition);
        }
        for (const auto &index_space : canonical_index_spaces) {
            rt->destroy_index_space(ctx, index_space);
        }
#endif // LEGION_SOLVERS_DISABLE_CLEANUP
    }

    Legion::Context get_context() const { return ctx; }
    Legion::Runtime *get_runtime() const { return rt; }

    std::size_t add_sol_vector(const PartitionedVector<ENTRY_T> &v) {
        assert(workspace_fields == Legion::FieldSpace::NO_SPACE);
        assert(workspace_regions.empty());
        assert(workspace_partitions.empty());
        assert(workspace_vectors.empty());
        const std::size_t idx = sol_vectors.size();
        if (canonical_index_spaces.size() > idx) {
            assert(canonical_index_spaces[idx] == v.get_index_space());
        } else {
            assert(canonical_index_spaces.size() == idx);
            rt->create_shared_ownership(ctx, v.get_index_space());
            canonical_index_spaces.push_back(v.get_index_space());
        }
        if (canonical_index_partitions.size() > idx) {
            assert(canonical_index_partitions[idx] == v.get_index_partition());
        } else {
            assert(canonical_index_partitions.size() == idx);
            const Legion::IndexPartition part = v.get_index_partition();
            assert(rt->is_index_partition_complete(part));
            assert(rt->is_index_partition_disjoint(part));
            rt->create_shared_ownership(ctx, part);
            canonical_index_partitions.push_back(part);
        }
        sol_vectors.push_back(
            std::make_unique<PartitionedVector<ENTRY_T>>(v)
        );
        return idx;
    }

    std::size_t add_rhs_vector(const PartitionedVector<ENTRY_T> &v) {
        assert(workspace_fields == Legion::FieldSpace::NO_SPACE);
        assert(workspace_regions.empty());
        assert(workspace_partitions.empty());
        assert(workspace_vectors.empty());
        const std::size_t idx = rhs_vectors.size();
        if (canonical_index_spaces.size() > idx) {
            assert(canonical_index_spaces[idx] == v.get_index_space());
        } else {
            assert(canonical_index_spaces.size() == idx);
            rt->create_shared_ownership(ctx, v.get_index_space());
            canonical_index_spaces.push_back(v.get_index_space());
        }
        if (canonical_index_partitions.size() > idx) {
            assert(canonical_index_partitions[idx] == v.get_index_partition());
        } else {
            assert(canonical_index_partitions.size() == idx);
            const Legion::IndexPartition part = v.get_index_partition();
            assert(rt->is_index_partition_complete(part));
            assert(rt->is_index_partition_disjoint(part));
            rt->create_shared_ownership(ctx, part);
            canonical_index_partitions.push_back(part);
        }
        rhs_vectors.push_back(
            std::make_unique<PartitionedVector<ENTRY_T>>(v)
        );
        return idx;
    }

    void allocate_workspace(std::size_t num_vectors) {
        assert(workspace_fields == Legion::FieldSpace::NO_SPACE);
        assert(workspace_regions.empty());
        assert(workspace_partitions.empty());
        assert(workspace_vectors.empty());
        const std::size_t num_spaces = canonical_index_spaces.size();
        assert(num_spaces == canonical_index_partitions.size());
        std::vector<std::size_t> field_sizes{};
        std::vector<Legion::FieldID> field_ids{};
        for (std::size_t i = 0; i < num_vectors; ++i) {
            field_sizes.push_back(sizeof(ENTRY_T));
            field_ids.push_back(static_cast<Legion::FieldID>(i));
        }
        workspace_fields =
            LegionSolvers::create_field_space(ctx, rt, field_sizes, field_ids);
        for (std::size_t i = 0; i < num_vectors; ++i) {
            workspace_vectors.emplace_back();
        }
        for (std::size_t i = 0; i < num_spaces; ++i) {
            workspace_regions.push_back(rt->create_logical_region(
                ctx, canonical_index_spaces[i], workspace_fields
            ));
            workspace_partitions.push_back(rt->get_logical_partition(
                ctx, workspace_regions.back(), canonical_index_partitions[i]
            ));
            for (std::size_t j = 0; j < num_vectors; ++j) {
                workspace_vectors[j].push_back(
                    std::make_unique<PartitionedVector<ENTRY_T>>(
                        ctx,
                        rt,
                        "workspace_" + std::to_string(j) + "_" +
                            std::to_string(i),
                        workspace_partitions[i],
                        static_cast<Legion::FieldID>(j)
                    )
                );
            }
        }
    }

    std::size_t get_num_spaces() const {
        const std::size_t num_spaces = canonical_index_spaces.size();
        assert(num_spaces == canonical_index_partitions.size());
        assert(
            workspace_regions.empty() ||
            (num_spaces == workspace_regions.size())
        );
        assert(
            workspace_partitions.empty() ||
            (num_spaces == workspace_partitions.size())
        );
        assert(num_spaces == sol_vectors.size());
        assert(num_spaces == rhs_vectors.size());
        for ([[maybe_unused]] const auto &v : workspace_vectors) {
            assert(num_spaces == v.size());
        }
        return num_spaces;
    }

    void add_row_partitioned_matrix(
        const AbstractMatrix<ENTRY_T> &matrix,
        std::size_t domain_index,
        std::size_t range_index
    ) {
        [[maybe_unused]] const std::size_t num_spaces = get_num_spaces();
        assert(domain_index < num_spaces);
        assert(range_index < num_spaces);
        row_partitioned_matrices.push_back(
            RowPartitionedMatrix{&matrix, domain_index, range_index}
        );
        row_partitioned_matrix_artifacts.push_back(
            build_row_partition_artifact(row_partitioned_matrices.back())
        );
    }

    void repartition(
        std::size_t space_index, Legion::IndexPartition new_partition
    ) {
        [[maybe_unused]] const std::size_t num_spaces = get_num_spaces();
        assert(space_index < num_spaces);
        assert(
            rt->get_parent_index_space(new_partition) ==
            canonical_index_spaces[space_index]
        );
        assert(rt->is_index_partition_complete(new_partition));
        assert(rt->is_index_partition_disjoint(new_partition));

        rt->create_shared_ownership(ctx, new_partition);
        const Legion::IndexPartition old_partition =
            canonical_index_partitions[space_index];

        destroy_row_partition_artifacts();
        canonical_index_partitions[space_index] = new_partition;

        rebuild_partitioned_vector(sol_vectors[space_index], new_partition);
        rebuild_partitioned_vector(rhs_vectors[space_index], new_partition);

        if (!workspace_regions.empty()) {
            workspace_partitions[space_index] = rt->get_logical_partition(
                ctx, workspace_regions[space_index], new_partition
            );
            for (auto &vectors : workspace_vectors) {
                rebuild_partitioned_vector(vectors[space_index], new_partition);
            }
        }

        rebuild_row_partition_artifacts();
        rt->destroy_index_partition(ctx, old_partition);
    }

    PartitionedVector<ENTRY_T> &
    get_vector(std::size_t vec_idx, std::size_t space_idx) {
        if (vec_idx == 0) {
            return *sol_vectors[space_idx];
        } else if (vec_idx == 1) {
            return *rhs_vectors[space_idx];
        } else {
            return *workspace_vectors[vec_idx - 2][space_idx];
        }
    }

    void zero_fill(std::size_t vec_idx) {
        if (vec_idx == 0) {
            for (auto &v : sol_vectors) { v->zero_fill(); }
        } else if (vec_idx == 1) {
            for (auto &v : rhs_vectors) { v->zero_fill(); }
        } else {
            for (auto &v : workspace_vectors[vec_idx - 2]) {
                v->zero_fill();
            }
        }
    }

    void copy(std::size_t dst_index, std::size_t src_index) {
        const std::size_t num_spaces = get_num_spaces();
        for (std::size_t i = 0; i < num_spaces; ++i) {
            get_vector(dst_index, i) = get_vector(src_index, i);
        }
    }

    void scal(std::size_t dst_index, Scalar<ENTRY_T> alpha) {
        const std::size_t num_spaces = get_num_spaces();
        for (std::size_t i = 0; i < num_spaces; ++i) {
            get_vector(dst_index, i).scal(alpha);
        }
    }

    void
    axpy(std::size_t dst_index, Scalar<ENTRY_T> alpha, std::size_t src_index) {
        const std::size_t num_spaces = get_num_spaces();
        for (std::size_t i = 0; i < num_spaces; ++i) {
            get_vector(dst_index, i).axpy(alpha, get_vector(src_index, i));
        }
    }

    void axpy(
        std::size_t dst_index,
        Scalar<ENTRY_T> numer,
        Scalar<ENTRY_T> denom,
        std::size_t src_index
    ) {
        const std::size_t num_spaces = get_num_spaces();
        for (std::size_t i = 0; i < num_spaces; ++i) {
            get_vector(dst_index, i)
                .axpy(numer, denom, get_vector(src_index, i));
        }
    }

    void axpy(
        std::size_t dst_index,
        Scalar<ENTRY_T> numer1,
        Scalar<ENTRY_T> numer2,
        Scalar<ENTRY_T> denom,
        std::size_t src_index
    ) {
        const std::size_t num_spaces = get_num_spaces();
        for (std::size_t i = 0; i < num_spaces; ++i) {
            get_vector(dst_index, i)
                .axpy(numer1, numer2, denom, get_vector(src_index, i));
        }
    }

    void
    xpay(std::size_t dst_index, Scalar<ENTRY_T> alpha, std::size_t src_index) {
        const std::size_t num_spaces = get_num_spaces();
        for (std::size_t i = 0; i < num_spaces; ++i) {
            get_vector(dst_index, i).xpay(alpha, get_vector(src_index, i));
        }
    }

    void xpay(
        std::size_t dst_index,
        Scalar<ENTRY_T> numer,
        Scalar<ENTRY_T> denom,
        std::size_t src_index
    ) {
        const std::size_t num_spaces = get_num_spaces();
        for (std::size_t i = 0; i < num_spaces; ++i) {
            get_vector(dst_index, i)
                .xpay(numer, denom, get_vector(src_index, i));
        }
    }

    Scalar<ENTRY_T> dot(std::size_t v_idx, std::size_t w_idx) {
        const std::size_t num_spaces = get_num_spaces();
        Scalar<ENTRY_T> result = get_vector(v_idx, 0).dot(get_vector(w_idx, 0));
        for (std::size_t i = 1; i < num_spaces; ++i) {
            result = result + get_vector(v_idx, i).dot(get_vector(w_idx, i));
        }
        return result;
    }

    void matvec(std::size_t dst_idx, std::size_t src_idx) {
        zero_fill(dst_idx);
        // TODO: count range index; request reduction privileges if > 1
        assert(
            row_partitioned_matrices.size() ==
            row_partitioned_matrix_artifacts.size()
        );
        for (std::size_t i = 0; i < row_partitioned_matrices.size(); ++i) {
            const RowPartitionedMatrix &matrix = row_partitioned_matrices[i];
            const RowPartitionedMatrixArtifacts &artifact =
                row_partitioned_matrix_artifacts[i];
            matrix.matrix->matvec(
                get_vector(dst_idx, matrix.range_index),
                get_vector(src_idx, matrix.domain_index),
                artifact.kernel_logical_partition,
                artifact.ghost_partition
            );
        }
    }

private:

    RowPartitionedMatrixArtifacts
    build_row_partition_artifact(const RowPartitionedMatrix &matrix) {
        const Legion::IndexPartition kernel_partition =
            matrix.matrix->create_kernel_partition_from_range_partition(
                canonical_index_partitions[matrix.range_index]
            );
        const Legion::IndexPartition ghost_partition =
            matrix.matrix->create_domain_partition_from_kernel_partition(
                canonical_index_spaces[matrix.domain_index], kernel_partition
            );
        return RowPartitionedMatrixArtifacts{
            kernel_partition,
            rt->get_logical_partition(
                matrix.matrix->get_kernel_region(), kernel_partition
            ),
            ghost_partition,
        };
    }

    void rebuild_row_partition_artifacts() {
        assert(row_partitioned_matrix_artifacts.empty());
        for (const RowPartitionedMatrix &matrix : row_partitioned_matrices) {
            row_partitioned_matrix_artifacts.push_back(
                build_row_partition_artifact(matrix)
            );
        }
    }

    void destroy_row_partition_artifacts() {
        for (const RowPartitionedMatrixArtifacts &artifact :
             row_partitioned_matrix_artifacts) {
            rt->destroy_index_partition(
                ctx, artifact.kernel_index_partition
            );
            rt->destroy_index_partition(ctx, artifact.ghost_partition);
        }
        row_partitioned_matrix_artifacts.clear();
    }

    void rebuild_partitioned_vector(
        std::unique_ptr<PartitionedVector<ENTRY_T>> &vector,
        Legion::IndexPartition new_partition
    ) {
        assert(vector);
        const Legion::LogicalPartition new_logical_partition =
            rt->get_logical_partition(
                ctx, vector->get_logical_region(), new_partition
            );
        vector = std::make_unique<PartitionedVector<ENTRY_T>>(
            ctx,
            rt,
            vector->get_name(),
            new_logical_partition,
            vector->get_fid()
        );
    }

}; // class SquarePlanner


} // namespace LegionSolvers


//         // mode 1: row-partitioned launch  V
//             // for each operator: ghost partition of each vector
//         // mode 2: tile-partitioned launch V x V
//             // for each operator: index subspace of V x V of nonempty tiles
//             // subregion of each vector piece
//         // mode 3: overapproximated launch K x V x V

//     }; // class SquarePlanner


#endif // LEGION_SOLVERS_SQUARE_PLANNER_HPP_INCLUDED
