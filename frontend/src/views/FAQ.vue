<template>
  <div>
    <faq-de v-if="$i18n.locale === 'de' || $i18n.locale === 'de-at'"></faq-de>
    <faq-en v-else></faq-en>
  </div>
</template>

<script>
import FaqDe from '../i18n/views/FAQ.de.vue'
import FaqEn from '../i18n/views/FAQ.en.vue'
import utils from '../utils'

export default {
  components: {
    FaqDe,
    FaqEn,
  },
  created: function() {
    utils.setTitle(this.$t('faq'))
  }
}
</script>
