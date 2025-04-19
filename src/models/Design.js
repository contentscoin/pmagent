import mongoose from 'mongoose';
const { Schema } = mongoose;

// 디자인 시스템 스키마
const designSystemSchema = new Schema({
  id: {
    type: String,
    required: true,
    unique: true
  },
  name: {
    type: String,
    required: true
  },
  description: {
    type: String
  },
  colors: {
    type: Map,
    of: String
  },
  typography: {
    type: Map,
    of: Map
  },
  spacing: {
    type: Map,
    of: Number
  }
});

// 디자인 스키마
const designSchema = new Schema({
  id: {
    type: String,
    required: true,
    unique: true
  },
  name: {
    type: String,
    required: true
  },
  type: {
    type: String,
    enum: ['component', 'screen', 'icon'],
    required: true
  },
  description: {
    type: String,
    required: true
  },
  designSystemId: {
    type: String,
    ref: 'DesignSystem'
  },
  properties: {
    type: Schema.Types.Mixed
  },
  assets: [{
    name: String,
    url: String,
    type: String
  }],
  createdBy: {
    type: String,
    default: 'designer_agent'
  },
  projectId: {
    type: String,
    ref: 'Project'
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
designSchema.index({ id: 1 }, { unique: true });
designSchema.index({ name: 1 });
designSchema.index({ projectId: 1 });
designSchema.index({ type: 1 });

const Design = mongoose.model('Design', designSchema);
const DesignSystem = mongoose.model('DesignSystem', designSystemSchema);

export { Design, DesignSystem }; 