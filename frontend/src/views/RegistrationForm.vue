<template>
  <div>
    <h2>Register</h2>
    <form @submit.prevent="registerUser">
      <div>
        <label for="email">Email</label>
        <input id="email" v-model="form.email" type="email" placeholder="Email" required />
        <span v-if="v$.form.email.$error" class="error-message">
          <span v-if="!v$.form.email.required">Email is required.</span>
          <span v-if="!v$.form.email.email">Please enter a valid email address.</span>
        </span>
      </div>
      <div>
        <label for="password">Password</label>
        <input id="password" v-model="form.password" type="password" placeholder="Password" required />
        <span v-if="v$.form.password.$error" class="error-message">
          <span v-if="!v$.form.password.required">Password is required.</span>
        </span>
      </div>
      <div>
        <label for="firstName">First Name</label>
        <input id="firstName" v-model="form.firstName" type="text" placeholder="First Name" required />
        <span v-if="v$.form.firstName.$error" class="error-message">
          <span v-if="!v$.form.firstName.required">First Name is required.</span>
        </span>
      </div>
      <div>
        <label for="lastName">Last Name</label>
        <input id="lastName" v-model="form.lastName" type="text" placeholder="Last Name" required />
        <span v-if="v$.form.lastName.$error" class="error-message">
          <span v-if="!v$.form.lastName.required">Last Name is required.</span>
        </span>
      </div>
      <div>
        <label for="displayName">Display Name</label>
        <input id="displayName" v-model="form.displayName" type="text" placeholder="Display Name" required />
        <span v-if="v$.form.displayName.$error" class="error-message">
          <span v-if="!v$.form.displayName.required">Display Name is required.</span>
        </span>
      </div>
      <div>
        <label for="city">City</label>
        <input id="city" v-model="form.city" type="text" placeholder="City" required />
        <span v-if="v$.form.city.$error" class="error-message">
          <span v-if="!v$.form.city.required">City is required.</span>
        </span>
      </div>
      <div>
        <label for="state">State</label>
        <input id="state" v-model="form.state" type="text" placeholder="State" required />
        <span v-if="v$.form.state.$error" class="error-message">
          <span v-if="!v$.form.state.required">State is required.</span>
        </span>
      </div>
      <div>
        <label for="zip">ZIP Code</label>
        <input id="zip" v-model="form.zip" type="text" placeholder="ZIP Code" required />
        <span v-if="v$.form.zip.$error" class="error-message">
          <span v-if="!v$.form.zip.required">ZIP Code is required.</span>
        </span>
      </div>
      <div>
        <label for="hasPets">Do you have pets?</label>
        <input id="hasPets" v-model="form.hasPets" type="checkbox" />
      </div>
      <div v-if="form.hasPets">
        <h3>Pet Information</h3>
        <div v-for="(pet, index) in form.pets" :key="index">
          <label :for="'petName' + index">Pet Name</label>
          <input :id="'petName' + index" v-model="pet.name" type="text" placeholder="Pet Name" />
          <!-- Add other pet fields here -->
        </div>
        <button type="button" @click="addPet">Add Another Pet</button>
      </div>
      <div v-if="successMessage" class="success-message">
        {{ successMessage }}
      </div>
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
      <button type="submit">Register</button>
    </form>
  </div>
</template>
<script>
import { useVuelidate } from '@vuelidate/core'
import { required, email } from '@vuelidate/validators'
import axios from 'axios'
import { useRouter } from 'vue-router' // Import useRouter

export default {
  setup() {
    const router = useRouter(); // Initialize the router
    const form = {
      email: '',
      password: '',
      firstName: '',
      lastName: '',
      displayName: '',
      city: '',
      state: '',
      zip: '',
      hasPets: false,
      pets: [{ name: '', type: '', age: null }]
    };

    const rules = {
      form: {
        email: { required, email },
        password: { required },
        firstName: { required },
        lastName: { required },
        displayName: { required },
        city: { required },
        state: { required },
        zip: { required }
      }
    };

    const v$ = useVuelidate(rules, { form });

    return { form, v$, router };
  },
  data() {
    return {
      successMessage: '',
      errorMessage: ''
    };
  },
  methods: {
    async registerUser() {
      console.log("Register User method called");
      this.v$.$touch(); // Touch all fields to trigger validation
      console.log("Form data before submission:", this.form);
      console.log("Validation state:", this.v$.$invalid);
      if (this.v$.$invalid) {
        console.log("Form is invalid, not submitting");
        console.log("Validation errors:", this.v$.$errors); // Log detailed validation errors
        return; // Stop execution if the form is invalid
      }

      try {
        const response = await axios.post('/users/', this.form);
        console.log("Registration successful", response);

        this.successMessage = 'Registration successful!';
        this.router.push('/login'); // Navigate to login on success
        this.form = {
          email: '',
          password: '',
          firstName: '',
          lastName: '',
          displayName: '',
          city: '',
          state: '',
          zip: '',
          hasPets: false,
          pets: [{ name: '', type: '', age: null }]
        }; // Reset form after successful registration
      } catch (error) {
        this.errorMessage = 'Registration failed. Please try again.';
        console.error("Registration error:", error.response ? error.response.data : error); // Log error details from server
      }
    },
    addPet() {
      this.form.pets.push({ name: '', type: '', age: null });
      console.log("Added new pet", this.form.pets); // Log action of adding a pet
    }
  }
}
</script>

