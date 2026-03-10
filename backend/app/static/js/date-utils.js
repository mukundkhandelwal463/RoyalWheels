/**
 * Date Utilities for RoyalWheels
 * Prevents users from selecting dates before today
 * Ensures return date is always after pickup date
 */

// Set minimum date to today for all date inputs on the page
function setMinDateToToday() {
  const today = new Date().toISOString().split('T')[0];
  const allDateInputs = document.querySelectorAll('input[type="date"]');
  
  allDateInputs.forEach(input => {
    input.setAttribute('min', today);
  });
}

// Setup date validation for pickup and return date pairs
// pickupId: ID of the pickup date input
// returnId: ID of the return date input
function setupDateValidation(pickupId, returnId) {
  const pickupInput = document.getElementById(pickupId);
  const returnInput = document.getElementById(returnId);
  
  if (pickupInput && returnInput) {
    pickupInput.addEventListener('change', () => {
      if (pickupInput.value) {
        // Set return date minimum to pickup date
        returnInput.setAttribute('min', pickupInput.value);
        
        // If return date is before pickup date, clear it
        if (returnInput.value && returnInput.value < pickupInput.value) {
          returnInput.value = '';
          
          // Trigger change event if there's a callback
          returnInput.dispatchEvent(new Event('change'));
        }
      }
    });
  }
}

// Initialize date restrictions when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  setMinDateToToday();
});
