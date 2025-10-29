<template>
  <div class="calendar-community-filter">
    <label for="community-filter" class="filter-label">{{ $t('calendar.communityFilter') }}:</label>
    <select 
      id="community-filter" 
      v-model="selectedCommunity" 
      @change="onFilterChange"
      class="form-control"
    >
      <option :value="null">{{ $t('calendar.allCommunities') }}</option>
      <option 
        v-for="community in communities" 
        :key="community.slug" 
        :value="community.slug"
      >
        {{ community.name }}
      </option>
    </select>
  </div>
</template>

<script>
import CommunitiesApi from '../../api/communities'

export default {
  data() {
    return {
      selectedCommunity: null,
      communities: []
    }
  },
  computed: {
    currentFilter() {
      return this.$store.getters.missionCalendarCommunityFilter
    }
  },
  mounted() {
    this.loadCommunities()
    this.selectedCommunity = this.currentFilter
  },
  methods: {
    async loadCommunities() {
      try {
        const response = await CommunitiesApi.getCommunities(1000, 0)
        if (response.data && response.data.communities) {
          this.communities = response.data.communities.sort((a, b) => 
            a.name.localeCompare(b.name)
          )
        }
      } catch (error) {
        console.error('Failed to load communities:', error)
      }
    },
    onFilterChange() {
      this.$store.dispatch('filterMissionCalendarByCommunity', this.selectedCommunity)
    }
  }
}
</script>

<style scoped>
.calendar-community-filter {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  margin-bottom: 0;
  font-weight: 500;
  white-space: nowrap;
}

.form-control {
  flex: 1;
  max-width: 300px;
}

@media (max-width: 767px) {
  .calendar-community-filter {
    flex-direction: column;
    align-items: stretch;
  }

  .form-control {
    max-width: 100%;
  }
}
</style>
