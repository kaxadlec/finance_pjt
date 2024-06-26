
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
const app = createApp(App)
const pinia = createPinia()

pinia.use(piniaPluginPersistedstate)
//환경변수 용 설정
app.use(pinia)

// app.use(createPinia())
app.use(router)

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'

import '@mdi/font/css/materialdesignicons.css' // Ensure you are using css-loader


const vuetify = createVuetify({
  icons: {
    defaultSet: 'mdi', // This is already the default value - only for display purposes
  },
  components,
  directives,
})


app.use(vuetify).mount('#app')
