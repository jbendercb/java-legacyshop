package com.example.legacyshop.repository;

import com.example.legacyshop.entity.Customer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * Repository for Customer entity operations.
 * 
 * Key patterns:
 * - Email-based lookup for customer identification
 * - Optional return types for null safety
 */
@Repository
public interface CustomerRepository extends JpaRepository<Customer, Long> {

    /**
     * Find customer by email (used for customer identification).
     */
    Optional<Customer> findByEmail(String email);

    /**
     * Check if email exists (for registration validation).
     */
    boolean existsByEmail(String email);
}