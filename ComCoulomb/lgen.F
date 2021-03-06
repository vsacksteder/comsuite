      subroutine lgen(bas,bmax,nv,nvmax,vecs,work)
c     generates lattice vectors
      use manager_mod
      use parallel_mod
      implicit none
      integer :: i,j,k,imax,jmax,kmax,nv,nvmax,m,iv,ilow,jv
      double precision ::
     $  bas(3,3),v(3),vecs(3,nvmax),work(*),bmax,bmax2,v2,vsm,
     &  alow,xx,ddd
      call latlim(bas,bmax,imax,jmax,kmax)
      bmax2=bmax*bmax
      nv=0
      do 20 i=-imax,imax
        do 20 j=-jmax,jmax
          do 20 k=-kmax,kmax
            do 21 m=1,3
 21           v(m)=i*bas(m,1)+j*bas(m,2)+k*bas(m,3)
            v2=v(1)*v(1)+v(2)*v(2)+v(3)*v(3)
            if(v2.gt.bmax2) goto 20
            nv=nv+1
            if(nv.gt.nvmax) then
              if(maswrk) write(iun,633) nvmax,i,imax
c              write(179,*) "calling ending in lgen.f"
              call ending
 633          format(/' --- nv=',i6,'  exceeded,   i=',i3,'  imax=',i3)
            endif
            do 22 m=1,3
 22           vecs(m,nv)=v(m)
            vsm=dabs(v(1))+dabs(v(2))+dabs(v(3))
            work(nv)=v2+vsm/1000.
 20   continue
c     --- sort by length -----------
      do 30 iv=1,nv
        ilow=iv
        alow=work(iv)
        do 31 jv=iv,nv
          if(work(jv).lt.alow) then
            alow=work(jv)
            ilow=jv
          endif
 31     continue
        if(ilow.eq.iv) goto 30
        do 32 m=1,3
          xx=vecs(m,iv)
          vecs(m,iv)=vecs(m,ilow)
 32       vecs(m,ilow)=xx
        work(ilow)=work(iv)
        xx=work(ilow)
 30   continue
c     ---- add neighbor layers if basis vec 3 is not in list ------
      do 41 iv=1,nv
        ddd=(bas(1,3)-vecs(1,iv))**2+(bas(2,3)-vecs(2,iv))**2
     .    +(bas(3,3)-vecs(3,iv))**2
        if(ddd.lt.1.d-8) return
 41   continue
c     write(31,650)
c     650 format(' basis vec 3 not in list - include 2 more planes')
      if(3*nv.gt.nvmax) then
        if(maswrk) write(6,643) nvmax
c        write(179,*) "calling ending in lgen.f"
        call ending
      endif
 643  format( '--- lgen needs nvmax at least',i7)
      do 40 iv=1,nv
        do 40 m=1,3
          vecs(m,iv+nv)=vecs(m,iv)+bas(m,3)
 40       vecs(m,iv+2*nv)=vecs(m,iv)-bas(m,3)
      nv=3*nv
      end


c     # latlim fortran *
      subroutine latlim(bas,vmax,i1,i2,i3)
c     limits in x y z direction, also initialize matrix
      implicit none
      integer :: i1,i2,i3,i,j
      double precision ::
     $  bas(3,3),a(3,3),a11,a22,a33,a12,a13,a23,det,vmax
      common /clatlm/ a11,a22,a33,a12,a13,a23
      do 6 i=1,3
        do 6 j=i,3
 6        a(i,j)=bas(1,i)*bas(1,j)+bas(2,i)*bas(2,j)+bas(3,i)*bas(3,j)
      a11=a(1,1)
      a12=a(1,2)
      a13=a(1,3)
      a22=a(2,2)
      a23=a(2,3)
      a33=a(3,3)
      det=a11*a22*a33+a12*a23*a13
     &  +a12*a23*a13-a13*a22*a13
     &  -a23*a23*a11-a12*a12*a33
      i1=vmax*dsqrt((a22*a33-a23**2)/det)
      i2=vmax*dsqrt((a11*a33-a13**2)/det)
      i3=vmax*dsqrt((a11*a22-a12**2)/det)
      end
