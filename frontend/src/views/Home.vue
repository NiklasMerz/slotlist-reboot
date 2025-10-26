<template>
  <div>
    <home-de v-if="$i18n.locale === 'de' || $i18n.locale === 'de-at'"></home-de>
    <home-en v-else></home-en>
    <calendar></calendar>
  </div>
</template>

<script>
import Calendar from '../components/Calendar.vue'
import HomeDe from '../i18n/views/Home.de.vue'
import HomeEn from '../i18n/views/Home.en.vue'
import utils from '../utils'

export default {
  components: {
    Calendar,
    HomeDe,
    HomeEn,
  },
  created: function() {
    utils.clearTitle()
  }
}
</script>
