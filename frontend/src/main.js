import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { setRouter } from './navigate'
import './styles.css'

setRouter(router)
createApp(App).use(router).mount('#app')
