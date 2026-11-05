package com.office.firezonepjt_admin.admin.jpa;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "admin_authority_history")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AdminAuthorityHistoryEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "aah_no")
    private int historyNo;

    @Column(name = "aah_admin_no", nullable = false)
    private int adminNo;

    @Column(name = "aah_before_auth_no")
    private Integer beforeAuthorityNo;

    @Column(name = "aah_after_auth_no", nullable = false)
    private int afterAuthorityNo;

    @Column(name = "aah_changed_by", nullable = false)
    private int changedBy;

    @Column(name = "aah_changed_at", nullable = false, columnDefinition = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    private LocalDateTime changedAt;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "aah_admin_no", insertable = false, updatable = false)
    private AdminEntity admin;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "aah_before_auth_no", insertable = false, updatable = false)
    private AdminAuthorityEntity beforeAuthority;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "aah_after_auth_no", insertable = false, updatable = false)
    private AdminAuthorityEntity afterAuthority;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "aah_changed_by", insertable = false, updatable = false)
    private AdminEntity changedByAdmin;
}
