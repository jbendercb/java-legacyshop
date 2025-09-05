package com.example.legacyshop.service;

import com.example.legacyshop.entity.Customer;
import com.example.legacyshop.exception.ResourceNotFoundException;
import com.example.legacyshop.repository.CustomerRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Service for Customer operations.
 * 
 * Key patterns:
 * - Find or create pattern for customer management
 * - Email-based customer identification
 */
@Service
@Transactional(readOnly = true)
public class CustomerService {

    private final CustomerRepository customerRepository;

    public CustomerService(CustomerRepository customerRepository) {
        this.customerRepository = customerRepository;
    }

    /**
     * Find customer by email, create if not exists.
     * Used in order creation to ensure customer exists.
     * Note: Participates in calling method's transaction for proper rollback.
     */
    public Customer findOrCreateCustomer(String email, String firstName, String lastName) {
        return customerRepository.findByEmail(email)
            .orElseGet(() -> {
                Customer customer = new Customer(email, firstName, lastName);
                return customerRepository.save(customer);
            });
    }

    /**
     * Find customer by email.
     */
    public Customer findByEmail(String email) {
        return customerRepository.findByEmail(email)
            .orElseThrow(() -> new ResourceNotFoundException("Customer not found with email: " + email));
    }

    /**
     * Get customer by ID.
     */
    public Customer getCustomer(Long id) {
        return customerRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Customer not found with id: " + id));
    }
}