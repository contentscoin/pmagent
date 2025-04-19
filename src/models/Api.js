import mongoose from 'mongoose';
const { Schema } = mongoose;

const apiSchema = new Schema({
  id: {
    type: String,
    required: true,
    unique: true
  },
  name: {
    type: String,
    required: true
  },
  path: {
    type: String,
    required: true
  },
  method: {
    type: String,
    enum: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
    required: true
  },
  description: {
    type: String,
    required: true
  },
  code: {
    type: String,
    required: true
  },
  parameters: [{
    name: String,
    type: String,
    required: Boolean,
    description: String
  }],
  responseSchema: {
    type: Schema.Types.Mixed
  },
  projectId: {
    type: String,
    ref: 'Project'
  },
  createdBy: {
    type: String,
    default: 'backend_agent'
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// 인덱스 설정
apiSchema.index({ id: 1 }, { unique: true });
apiSchema.index({ name: 1 });
apiSchema.index({ projectId: 1 });
apiSchema.index({ path: 1, method: 1 }, { unique: true });

const Api = mongoose.model('Api', apiSchema);

export default Api; 