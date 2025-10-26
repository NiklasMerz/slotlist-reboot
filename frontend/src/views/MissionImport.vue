<template>
  <div class="container">
    <div class="row">
      <div class="col">
        <h3>Import Mission from slotlist.info</h3>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <b-form @submit.stop.prevent="submitMissionImport">
          <div class="row">
            <div class="col">
              <b-form-fieldset label="Mission Slug" :state="missionSlugState" :feedback="missionSlugFeedback" description="Enter the slug of the mission to import from slotlist.info">
                <b-form-input v-model="missionSlug" type="text" required placeholder="e.g., bf-mm-20251028"></b-form-input>
              </b-form-fieldset>
            </div>
          </div>
          <div class="row">
            <div class="col text-center">
              <b-form-fieldset label="Preview Only (Dry Run)" state="success" description="Check this to preview the import without actually saving it">
                <b-form-checkbox v-model="dryRun"></b-form-checkbox>
              </b-form-fieldset>
            </div>
          </div>
        </b-form>
      </div>
    </div>
    <div class="row">
      <div class="col text-center">
        <b-btn variant="primary" @click="submitMissionImport" :disabled="importing">
          <i class="fa" :class="importing ? 'fa-spinner fa-spin' : 'fa-download'" aria-hidden="true"></i> {{ importing ? 'Importing...' : 'Import Mission' }}
        </b-btn>
      </div>
    </div>
    <div v-if="importResult" class="row mt-3">
      <div class="col">
        <div v-if="importResult.success" class="alert alert-success">
          <h4>Import Successful!</h4>
          <p>{{ importResult.message }}</p>
          <p><strong>Mission:</strong> {{ importResult.mission_title }}</p>
          <p><strong>Slug:</strong> {{ importResult.mission_slug }}</p>
          <router-link :to="'/missions/' + importResult.mission_slug" class="btn btn-success">
            View Mission
          </router-link>
        </div>
        <div v-if="importResult.preview" class="alert alert-info">
          <h4>Import Preview</h4>
          <p><strong>Title:</strong> {{ importResult.preview.title }}</p>
          <p><strong>Description:</strong> {{ importResult.preview.description }}</p>
          <p><strong>Start Time:</strong> {{ importResult.preview.start_time }}</p>
          <p><strong>Slot Groups:</strong> {{ importResult.preview.slot_groups_count }}</p>
          <p><strong>Total Slots:</strong> {{ importResult.preview.total_slots }}</p>
        </div>
        <div v-if="importError" class="alert alert-danger">
          <h4>Import Failed</h4>
          <p>{{ importError }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import utils from '../utils'

export default {
  data() {
    return {
      missionSlug: null,
      dryRun: false,
      importing: false,
      importResult: null,
      importError: null
    }
  },
  computed: {
    missionSlugState() {
      return _.isNil(this.missionSlug) || _.isEmpty(this.missionSlug) ? 'danger' : 'success'
    },
    missionSlugFeedback() {
      return _.isNil(this.missionSlug) || _.isEmpty(this.missionSlug) ? 'Mission slug is required' : ''
    }
  },
  methods: {
    async submitMissionImport() {
      if (_.isNil(this.missionSlug) || _.isEmpty(this.missionSlug)) {
        return
      }

      this.importing = true
      this.importResult = null
      this.importError = null

      try {
        const response = await axios.post('/v1/import', {
          slug: this.missionSlug,
          dry_run: this.dryRun
        })

        this.importResult = response.data

        if (this.importResult.success) {
          this.$store.dispatch('setAlert', {
            showAlert: true,
            alertVariant: 'success',
            alertMessage: `Mission imported successfully: ${this.importResult.mission_title}`
          })
        }
      } catch (error) {
        console.error('Import failed:', error)
        this.importError = (error.response && error.response.data && error.response.data.detail) || error.message || 'Import failed'
        this.$store.dispatch('setAlert', {
          showAlert: true,
          alertVariant: 'danger',
          alertMessage: this.importError
        })
      } finally {
        this.importing = false
      }
    }
  },
  created: function() {
    utils.setTitle('Import Mission')
  }
}
</script>

