<template>
  <div class="calendar-community-filter">
    <label for="community-filter" class="filter-label">{{ $t('calendar.communityFilter') }}:</label>
    <div class="community-filter-dropdown" :class="{'show': showDropdown}">
      <input
        id="community-filter"
        type="text"
        v-model="searchQuery"
        @focus="showDropdown = true"
        @blur="hideDropdown"
        @input="onSearchInput"
        @keydown.down="navigateDown"
        @keydown.up="navigateUp"
        @keydown.enter="selectHighlighted"
        @keydown.esc="closeDropdown"
        :placeholder="selectedCommunityName || $t('calendar.allCommunities')"
        class="form-control"
        autocomplete="off"
      />
      <div class="dropdown-menu" :class="{'show': showDropdown}" v-if="filteredCommunities.length > 0 || searchQuery">
        <button
          type="button"
          class="dropdown-item"
          :class="{'active': highlightedIndex === -1}"
          @mousedown.prevent="selectCommunity(null)"
          @mouseenter="highlightedIndex = -1"
        >
          {{ $t('calendar.allCommunities') }}
        </button>
        <button
          type="button"
          class="dropdown-item"
          :class="{'active': highlightedIndex === index}"
          v-for="(community, index) in filteredCommunities"
          :key="community.slug"
          @mousedown.prevent="selectCommunity(community.slug)"
          @mouseenter="highlightedIndex = index"
        >
          <span v-if="community.tag" class="community-tag-dropdown">[{{ community.tag }}]</span>
          {{ community.name }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import CommunitiesApi from '../../api/communities'

export default {
  data() {
    return {
      selectedCommunity: null,
      communities: [],
      searchQuery: '',
      showDropdown: false,
      highlightedIndex: -1
    }
  },
  computed: {
    currentFilter() {
      return this.$store.getters.missionCalendarCommunityFilter
    },
    selectedCommunityName() {
      if (!this.selectedCommunity) return null
      const community = this.communities.find(c => c.slug === this.selectedCommunity)
      return community ? community.name : null
    },
    filteredCommunities() {
      if (!this.searchQuery) {
        return this.communities
      }
      const query = this.searchQuery.toLowerCase()
      return this.communities.filter(community => 
        community.name.toLowerCase().includes(query) ||
        (community.tag && community.tag.toLowerCase().includes(query))
      )
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
    selectCommunity(slug) {
      this.selectedCommunity = slug
      this.searchQuery = ''
      this.showDropdown = false
      this.$store.dispatch('filterMissionCalendarByCommunity', slug)
    },
    onSearchInput() {
      this.showDropdown = true
      this.highlightedIndex = -1
    },
    hideDropdown() {
      setTimeout(() => {
        this.showDropdown = false
        this.searchQuery = ''
      }, 200)
    },
    closeDropdown() {
      this.showDropdown = false
      this.searchQuery = ''
    },
    navigateDown() {
      if (this.highlightedIndex < this.filteredCommunities.length - 1) {
        this.highlightedIndex++
      }
    },
    navigateUp() {
      if (this.highlightedIndex > -1) {
        this.highlightedIndex--
      }
    },
    selectHighlighted() {
      if (this.highlightedIndex === -1) {
        this.selectCommunity(null)
      } else if (this.highlightedIndex >= 0 && this.highlightedIndex < this.filteredCommunities.length) {
        this.selectCommunity(this.filteredCommunities[this.highlightedIndex].slug)
      }
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

.community-filter-dropdown {
  flex: 1;
  max-width: 300px;
  position: relative;
}

.form-control {
  width: 100%;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 2px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.dropdown-menu.show {
  display: block;
}

.dropdown-item {
  text-align: left;
  width: 100%;
  border: none;
  background: none;
  padding: 8px 12px;
  cursor: pointer;
  color: #333;
}

.dropdown-item:hover,
.dropdown-item.active {
  background-color: #f5f5f5;
  color: #333;
}

.community-tag-dropdown {
  font-weight: 600;
  color: #367016;
  margin-right: 6px;
}

@media (max-width: 767px) {
  .calendar-community-filter {
    flex-direction: column;
    align-items: stretch;
  }

  .community-filter-dropdown {
    max-width: 100%;
  }
}
</style>
