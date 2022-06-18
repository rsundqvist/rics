SELECT customer_id,
       inventory.film_id,
       staff_id,
       store_id,
       rental_date,
       return_date
FROM rental
LEFT JOIN inventory ON rental.inventory_id = inventory.inventory_id;
